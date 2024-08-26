import pika
import threading
import logging
from datetime import datetime, timedelta
from typing import Callable
from keycloak.keycloak_openid import KeycloakOpenID
import getpass
import ssl
from keycloak.exceptions import KeycloakAuthenticationError
import functools

from .schemas import ReadyStatus
from .simulator import Simulator
from .application_utils import (
    ConnectionConfig,
    TimeStatusPublisher,
    ModeStatusObserver,
    ShutDownObserver,
)

logger = logging.getLogger(__name__)

class Application:
    def __init__(self, app_name: str, app_description: str = None):
        self.simulator = Simulator()
        self.connection = None
        self.channel = None
        self.prefix = None
        self.app_name = app_name
        self.app_description = app_description
        self._time_status_publisher = None
        self._mode_status_observer = None
        self._shut_down_observer = None
        self._is_connected = threading.Event()
        self._should_stop = threading.Event()
        self.consuming = False
        self.closing = False

    def ready(self) -> None:
        status = ReadyStatus.parse_obj(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )

        # Declare topic and queue names
        topic = f"{self.prefix}.{self.app_name}.status.ready"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        # Declare a queue and bind it to the exchange with the routing key
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")
        
        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic, #f"{self.prefix}.{self.app_name}.status.ready",
            body=status.json(by_alias=True, exclude_none=True),
            properties=pika.BasicProperties(expiration='30000')
        )

    def new_access_token(self, config, refresh_token=None):

        keycloak_openid = KeycloakOpenID(server_url=f'{'http' if 'localhost' in config.host else 'https'}://{config.host}:{config.keycloak_port}', #"http://localhost:8080/",
                                        client_id=config.client_id,
                                        realm_name="test",
                                        client_secret_key=config.client_secret_key
                                        )

        try:
            if refresh_token:
                token = keycloak_openid.refresh_token(refresh_token)
            else:
                # Attempt to get token without OTP
                try:
                    token = keycloak_openid.token(grant_type='password', 
                                                username=config.username, 
                                                password=config.password)
                                                # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')
                except KeycloakAuthenticationError as e:

                    logger.error(f"Authentication error without OTP: {e}")
                    otp = input("Enter OTP: ")
                    token = keycloak_openid.token(grant_type='password', 
                                                username=config.username, 
                                                password=config.password, 
                                                totp=otp)
                                                # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')

            if 'access_token' in token:
                logger.info("Access token successfully acquired.")
                logger.info(f"Access token scopes: {token['scope']}")
                return token['access_token'], token['refresh_token']
            else:
                raise Exception("Error: The request was unsuccessful.")
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def start_up(
        self,
        prefix: str,
        config: ConnectionConfig,
        set_offset: bool = True,
        time_status_step: timedelta = None,
        time_status_init: datetime = None,
        shut_down_when_terminated: bool = False,
    ) -> None:
        if set_offset:
            self.set_wallclock_offset()
        self.prefix = prefix

        # credentials = pika.PlainCredentials(config.username, config.password)
        # parameters = pika.ConnectionParameters(
        #     host=config.host,
        #     port=config.rabbitmq_port,
        #     credentials=credentials,
        #     ssl_options=pika.SSLOptions() if config.is_tls else None,
        # )
        
        # Obtain access token and refresh token
        access_token, refresh_token = self.new_access_token(config)

        # Set up connection parameters
        parameters = pika.ConnectionParameters(
            host=config.host,
            virtual_host=config.virtual_host,
            port=config.rabbitmq_port,
            credentials=pika.PlainCredentials('', access_token),
            heartbeat=600
        )

        def on_connection_open(connection):
            self.connection = connection
            self.connection.channel(on_open_callback=self.on_channel_open)
            logger.info("Connection established successfully.")

        self.connection = pika.SelectConnection(
            parameters=parameters,
            on_open_callback=on_connection_open,
            on_open_error_callback=self.on_connection_error,
            on_close_callback=self.on_connection_closed,
        )
    
        # Start Pika's event loop in a separate thread
        connection_thread = threading.Thread(target=self.start_event_loop)
        connection_thread.start()

        # Wait for the connection to be established
        self._is_connected.wait()
        
        # Configure observers
        self._create_time_status_publisher(time_status_step, time_status_init)
        self._create_mode_status_observer()
        if shut_down_when_terminated:
            self._create_shut_down_observer()

        logger.info(f"Application {self.app_name} successfully started up.")

    def start_event_loop(self):
        # self.connection.ioloop.start()
        while True:
            try:
                # pass
                self.connection.ioloop.start()
                # self.run()
                # self._start_event_loop()
            except KeyboardInterrupt:
                self.stop()
                break
            # self._maybe_reconnect()

    def on_channel_open(self, channel):
        self.channel = channel
        # Signal that connection is established
        self._is_connected.set()
        # Declare necessary exchanges, queues, and bindings
        # For example: self.channel.exchange_declare(exchange='logs', exchange_type='topic')

    def on_connection_error(self, connection, error):
        logger.error(f"Connection error: {error}")
        self._is_connected.clear()

    def on_connection_closed(self, connection, reason):
        logger.info(f"Connection closed: {reason}")
        self._is_connected.clear()
        if not self._should_stop.is_set():
            # Try to reconnect if not shutting down
            self.start_up(self.prefix, self.connection_parameters)

    def shut_down(self) -> None:
        self._should_stop.set()
        if self._time_status_publisher is not None:
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None
        if self.connection:
            self.connection.close()
        logger.info(f"Application {self.app_name} successfully shut down.")

    def send_message(self, app_topic: str, payload: str) -> None:
        # Declare topic and queue names
        topic = f"{self.prefix}.{self.app_name}.{app_topic}"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        # Declare a queue and bind it to the exchange with the routing key
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")

        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=topic,
            body=payload,
            properties=pika.BasicProperties(expiration='30000')
        )
###
    def add_message_callback(self, app_name: str, app_topic: str, user_callback: Callable):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        topic = f"{self.prefix}.{app_name}.{app_topic}"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        combined_cb = self.combined_callback(user_callback)


        # Declare the exchange
        # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # # Declare the queue, 60000 milliseconds = 60 seconds 
        self.channel.queue_declare(queue=queue_name, durable=True) #, arguments={'x-message-ttl': 60000})
        
        # Bind the queue to the exchange with the routing key
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)
        
        # Set QoS settings
        self.channel.basic_qos(prefetch_count=1)

        self._consumer_tag = self.channel.basic_consume(
            queue=topic,
            on_message_callback=combined_cb,
            auto_ack=False)
        
        logger.debug(f"Subscribing and adding callback to topic: {topic}")

        self.was_consuming = True
        self.consuming = True

        # self.remove_message_callback()

    def combined_callback(self, user_callback):
        def wrapper(ch, method, properties, body): #_unused_channel, basic_deliver, properties, body):
            # Call the on_message method
            self.on_message(ch, method, properties, body) #_unused_channel, basic_deliver, properties, body)
            # Call the user-provided callback
            user_callback(ch, method, properties, body) #_unused_channel, basic_deliver, properties, body)
        return wrapper


    # def add_message_callback(self, app_name: str, app_topic: str): #, callback: Callable):
    #     """This method sets up the consumer by first calling
    #     add_on_cancel_callback so that the object is notified if RabbitMQ
    #     cancels the consumer. It then issues the Basic.Consume RPC command
    #     which returns the consumer tag that is used to uniquely identify the
    #     consumer with RabbitMQ. We keep the value to use it when we want to
    #     cancel consuming. The on_message method is passed in as a callback pika
    #     will invoke when a message is fully received.

    #     """
    #     routing_key = f"{self.prefix}.{app_name}.{app_topic}"

    #     logger.info('Issuing consumer related RPC commands')
    #     self.add_on_cancel_callback()
    #     self._consumer_tag = self.channel.basic_consume(
    #         routing_key, self.on_message)
    #     self.was_consuming = True
    #     self.consuming = True

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        logger.info('Adding consumer cancellation callback')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        logger.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        self.channel.close()

    def on_message(self, ch, method, properties, body): #, _unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body

        """
        logger.debug(f'Received message # {method.delivery_tag}: {body.decode('utf8')}')
        self.acknowledge_message(method.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        try:
            logger.debug(f'Acknowledging message {delivery_tag}')
            self.channel.basic_ack(delivery_tag)
        except:
            pass

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self.channel:
            logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                self.on_cancelok, userdata=self._consumer_tag)
            self.channel.basic_cancel(self._consumer_tag, cb)

    # def run(self):
    #     """Run the example consumer by connecting to RabbitMQ and then
    #     starting the IOLoop to block and allow the SelectConnection to operate.

    #     """
    #     # self.connection = self.connect()
    #     self.connection.ioloop.start()
    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)

        """
        self.consuming = False
        logger.info(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        self.close_channel()
        self.stop_loop()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        logger.info('Closing the channel')
        self.channel.close()

    def stop_loop(self):
        """Stop the IO loop
        """
        self.connection.ioloop.stop()
        # self.connection.ioloop.clo

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        if not self.closing:
            self.closing = True
            logger.info('Stopping')
            if self.consuming:
                self.stop_consuming()
                self.connection.ioloop.start()
            else:
                self.connection.ioloop.stop()
            logger.info('Stopped')

    # def nonblocking_consume(self):
    #     while True:
    #         try:
    #             pass
    #             # self.run()
    #             # self._start_event_loop()
    #         except KeyboardInterrupt:
    #             self.stop()
    #             break
    #         # self._maybe_reconnect()

###
    # def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
    #     routing_key = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.info(f"Setting up consumer for routing key: {routing_key}")

    #     # def pika_callback(ch, method, properties, body):
    #     #     callback(ch, method, properties, body)#body)

    #     self.channel.basic_consume(queue=routing_key, on_message_callback=callback, auto_ack=False) #True)

    # def remove_message_callback(self, app_name: str, app_topic: str) -> None:
    #     routing_key = f"{self.prefix}.{app_name}.{app_topic}"
    #     logger.debug(f"Removing consumer for routing key: {routing_key}")
    #     self.channel.basic_cancel(routing_key)

    def remove_message_callback(self):
        """This method cancels the consumer by issuing the Basic.Cancel RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. It also ensures that the consumer is no longer
        consuming messages.

        """
        if self._consumer_tag:
            logger.info('Cancelling the consumer')
            # self.channel.basic_cancel(self._consumer_tag)
            self.stop()
            self._consumer_tag = None
            self.was_consuming = False
            self.consuming = False
            logger.debug('Consumer cancelled successfully')
        else:
            logger.warning('No consumer to cancel')


    def set_wallclock_offset(self, host="pool.ntp.org", retry_delay_s: int = 5, max_retry: int = 5) -> None:
        # Implementation for setting wallclock offset
        pass

    # Helper methods for creating and managing observers
    def _create_time_status_publisher(self, time_status_step: timedelta, time_status_init: datetime) -> None:
        if time_status_step is not None:
            if self._time_status_publisher is not None:
                self.simulator.remove_observer(self._time_status_publisher)
            self._time_status_publisher = TimeStatusPublisher(self, time_status_step, time_status_init)
            self.simulator.add_observer(self._time_status_publisher)

    def _create_mode_status_observer(self) -> None:
        if self._mode_status_observer is not None:
            self.simulator.remove_observer(self._mode_status_observer)
        self._mode_status_observer = ModeStatusObserver(self)
        self.simulator.add_observer(self._mode_status_observer)

    def _create_shut_down_observer(self) -> None:
        if self._shut_down_observer is not None:
            self.simulator.remove_observer(self._shut_down_observer)
        self._shut_down_observer = ShutDownObserver(self)
        self.simulator.add_observer(self._shut_down_observer)

    def declare_bind_queue(self, prefix, manager_app_name, queue) -> None:
        topic = f"{prefix}.{manager_app_name}.{queue}"
        queue_name = f"{topic}.{self.app_name}" #topic #f"{topic}.{self.app_name}"
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)


# """
# Provides a base application that publishes messages from a simulator to a broker.
# """

# from datetime import datetime, timedelta
# import logging

# import pika.channel
# import pika.connection
# import ntplib
# import paho.mqtt.client as mqtt
# import time
# from typing import Callable
# import threading

# import pika
# from datetime import timedelta, datetime
# import requests
# import sys
# from keycloak.keycloak_openid import KeycloakOpenID
# import getpass
# import ssl
# from keycloak.exceptions import KeycloakAuthenticationError

# from .schemas import ReadyStatus
# from .simulator import Simulator
# from .application_utils import (
#     ConnectionConfig,
#     TimeStatusPublisher,
#     ModeStatusObserver,
#     ShutDownObserver,
# )

# logger = logging.getLogger(__name__)


# class Application(object):
#     """
#     Base class for a member application.

#     This object class defines the main functionality of a NOS-T application which can be modified for user needs.

#     Attributes:
#         prefix (str): The test run namespace (prefix)
#         simulator (:obj:`Simulator`): Application simulator -- calls on the simulator.py class for functionality
#         client (:obj:`Client`): Application MQTT client
#         app_name (str): Test run application name
#         app_description (str): Test run application description (optional)
#         time_status_step (:obj:`timedelta`): Scenario duration between time status messages
#         time_status_init (:obj:`datetime`): Scenario time of first time status message
#     """

#     def __init__(self, app_name: str, app_description: str = None): #,config: ConnectionConfig, 
#         """
#         Initializes a new application.

#         Args:
#             app_name (str): application name
#             app_description (str): application description (optional)
#         """
#         self.simulator = Simulator()
#         self.channel = pika.channel
#         self.connection = pika.connection
#         self.prefix = None
#         self.app_name = app_name
#         self.app_description = app_description
#         self._time_status_publisher = None
#         self._mode_status_observer = None
#         self._shut_down_observer = None

#         # # Obtain access token and refresh token
#         # access_token, refresh_token = self.new_access_token(config)

#         # # Set up connection parameters
#         # parameters = pika.ConnectionParameters(
#         #     host=config.host,
#         #     virtual_host=config.virtual_host,
#         #     port=config.rabbitmq_port,
#         #     credentials=pika.PlainCredentials('', access_token),
#         #     heartbeat=600
#         # )

#         # # Configure transport layer security (TLS) if needed
#         # if config.is_tls:
#         #     logger.info("Using TLS/SSL.")
#         #     context = ssl.create_default_context()
#         #     parameters.ssl_options = pika.SSLOptions(context)

#         # # Connect to server
#         # try:
#         #     self.connection = pika.BlockingConnection(parameters)
#         #     self.channel = self.connection.channel()
#         #     logger.info("Connection established successfully.")
#         # except pika.exceptions.ProbableAccessDeniedError as e:
#         #     logger.info(f"Access denied: {e}")
#         #     sys.exit(1)

#     def ready(self) -> None:
#         """
#         Signals the application is ready to initialize scenario execution.
#         Publishes a :obj:`ReadyStatus` message to the topic `prefix/app_name/status/ready`.
#         """
#         # publish ready status message
#         status = ReadyStatus.parse_obj(
#             {
#                 "name": self.app_name,
#                 "description": self.app_description,
#                 "properties": {"ready": True},
#             }
#         )
        
#         # self.client.publish(
#         #     f"{self.prefix}/{self.app_name}/status/ready",
#         #     status.json(by_alias=True, exclude_none=True),
#         # )
        
#         # Push to start_up()
#         topic = f"{self.prefix}.{self.app_name}.status.ready"
#         queue_name = topic #".".join(topic.split(".") + ["queue"]) 
#         ###

#         # Declare the topic exchange
#         # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')
        
#         # Declare a queue and bind it to the exchange with the routing key
#         self.channel.queue_declare(queue=queue_name, durable=True)
#         self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)

#         # Expiration of 60000 ms = 60 sec
#         self.channel.basic_publish(
#             exchange=self.prefix,
#             routing_key=topic,
#             body=status.json(by_alias=True, exclude_none=True),
#             properties=pika.BasicProperties(expiration='30000')
#         )
        
#         logger.info(f'Application "{self.app_name}" successfully sent ready message.')

#     def new_access_token(self, config, refresh_token=None):

#         keycloak_openid = KeycloakOpenID(server_url=f'{'http' if 'localhost' in config.host else 'https'}://{config.host}:{config.keycloak_port}', #"http://localhost:8080/",
#                                         client_id=config.client_id,
#                                         realm_name="test",
#                                         client_secret_key=config.client_secret_key
#                                         )

#         try:
#             if refresh_token:
#                 token = keycloak_openid.refresh_token(refresh_token)
#             else:
#                 # Attempt to get token without OTP
#                 try:
#                     token = keycloak_openid.token(grant_type='password', 
#                                                 username=config.username, 
#                                                 password=config.password)
#                                                 # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')
#                 except KeycloakAuthenticationError as e:

#                     logger.error(f"Authentication error without OTP: {e}")
#                     otp = input("Enter OTP: ")
#                     token = keycloak_openid.token(grant_type='password', 
#                                                 username=config.username, 
#                                                 password=config.password, 
#                                                 totp=otp)
#                                                 # scope='openid rabbitmq.read:*/nost/nost.* rabbitmq.write:*/nost/nost.* rabbitmq.configure:*/nost/nost.*')

#             if 'access_token' in token:
#                 logger.info("Access token successfully acquired.")
#                 logger.info(f"Access token scopes: {token['scope']}")
#                 return token['access_token'], token['refresh_token']
#             else:
#                 raise Exception("Error: The request was unsuccessful.")
            
#         except Exception as e:
#             logger.error(f"An error occurred: {e}")
#             raise

#     def start_up(
#         self,
#         prefix: str,
#         config: ConnectionConfig,
#         set_offset: bool = True,
#         time_status_step: timedelta = None,
#         time_status_init: datetime = None,
#         shut_down_when_terminated: bool = False,
#     ) -> None:
#         # Maybe configure wallclock offset
#         if set_offset:
#             self.set_wallclock_offset()

#         # Set test run prefix
#         self.prefix = prefix
#         access_token, refresh_token = self.new_access_token(config)
#         parameters = pika.ConnectionParameters(
#                 host=config.host,
#                 virtual_host=config.virtual_host,
#                 port=config.rabbitmq_port,
#                 credentials=pika.PlainCredentials('', access_token))

#         # Configure transport layer security (TLS) if needed
#         if config.is_tls:
#             logger.info("Using TLS/SSL.")
#             context = ssl.create_default_context()
#             parameters.ssl_options = pika.SSLOptions(context)

#         # Connect to server
#         try:
#             self.connection = pika.BlockingConnection(parameters)
#             logger.info("Connection established successfully.")
#         except pika.exceptions.ProbableAccessDeniedError as e:
#             logger.info(f"Access denied: {e}")
#             sys.exit(1)

#         self.channel = self.connection.channel()

#         # Declare the topic exchange
#         self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')
        
#         # Configure observers
#         self._create_time_status_publisher(time_status_step, time_status_init)
#         self._create_mode_status_observer()
#         if shut_down_when_terminated:
#             self._create_shut_down_observer()

#         logger.info(f'Application "{self.app_name}" successfully started up.')

#     def _create_time_status_publisher(
#         self, time_status_step: timedelta, time_status_init: datetime
#     ) -> None:
#         """
#         Creates a new time status publisher to publish the time status when it changes.

#         Args:
#             time_status_step (:obj:`timedelta`): scenario duration between time status messages
#             time_status_init (:obj:`datetime`): scenario time for first time status message
#         """
#         if time_status_step is not None:
#             if self._time_status_publisher is not None:
#                 self.simulator.remove_observer(self._time_status_publisher)
#             self._time_status_publisher = TimeStatusPublisher(
#                 self, time_status_step, time_status_init
#             )
#             self.simulator.add_observer(self._time_status_publisher)

#     def _create_mode_status_observer(self) -> None:
#         """
#         Creates a mode status observer to publish the mode status when it changes.
#         """
#         if self._mode_status_observer is not None:
#             self.simulator.remove_observer(self._mode_status_observer)
#         self._mode_status_observer = ModeStatusObserver(self)
#         self.simulator.add_observer(self._mode_status_observer)

#     def _create_shut_down_observer(self) -> None:
#         """
#         Creates an observer to shut down the application when the simulation is terminated.
#         """
#         if self._shut_down_observer is not None:
#             self.simulator.remove_observer(self._shut_down_observer)
#         self._shut_down_observer = ShutDownObserver(self)
#         self.simulator.add_observer(self._shut_down_observer)

#     def shut_down(self) -> None:
#         """
#         Shuts down the application by stopping the background event loop and disconnecting from the broker.
#         """
#         if self._time_status_publisher is not None:
#             # remove the time status observer
#             self.simulator.remove_observer(self._time_status_publisher)
#         self._time_status_publisher = None
        
#         # close the connection
#         # if self.client.is_open:
#         #     self.client.close()
        
#         # if self.channel.is_open:
#         #     self.channel.close()

#         # if self.connection.is_open:
#         #     self.connection.close()
        
#         # if self.channel.is_closed and self.connection.is_closed:
#         #     # clear prefix
#         #     # self.prefix = None
#         #     logger.info(f'Application "{self.app_name}" successfully shut down.')

#     def send_message(self, app_topic: str, payload: str) -> None:
#         """
#         Sends a message with payload `payload` to the topic `prefix/app_name/app_topic`.

#         Args:
#             app_topic (str): application topic
#             payload (str): message payload (JSON-encoded string)

#         """
        
#         # Part of start_up(): Define all queues that should be declared (time.status, .ready, etc.)
#         # Take one position or other declared in advance or latest possible moment (choose one, I will decide which makes more sense based on users [easier to use may be preferred by users])
#         topic = f"{self.prefix}.{self.app_name}.{app_topic}"
#         queue_name = topic #".".join(topic.split(".") + ["queue"]) 

#         # Declare a queue and bind it to the exchange with the routing key
#         self.channel.queue_declare(queue=queue_name, durable=True)
#         self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")

#         # Expiration of 60000 ms = 60 sec
#         self.channel.basic_publish(
#             exchange=self.prefix,
#             routing_key=topic,
#             # routing_key=f"{self.prefix}.{self.app_name}.status.time",
#             body=payload,
#             properties=pika.BasicProperties(expiration='30000')
#         )

#         logger.info(f"Successfully sent message {topic}: {payload}")

#     def add_message_callback(self, app_name: str, app_topic: str, callback: Callable) -> None:
#         """
#         Adds a message callback for application name and topic `prefix.app_name.app_topic`.

#         Args:
#             app_name (str): The application name
#             app_topic (str): The application topic
#             callback (Callable): The callback function to handle messages
#         """
#         topic = f"{self.prefix}.{app_name}.{app_topic}"
#         queue_name = topic #".".join(topic.split(".") + ["queue"]) 


#         # Can manager miss messages becuase other apps are subscribing to topic meant for manager
#         # Specific destination (auto ack, or not)
#         # Quality 
#         # Send_message(): Set up the queue
#         # print(f'Queue: {queue_name}')
#         logger.info(f"Subscribing and adding callback to topic: {topic}")
        
#         # Declare the exchange
#         # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

#         # # Declare the queue, 60000 milliseconds = 60 seconds 
#         self.channel.queue_declare(queue=queue_name, durable=True) #, arguments={'x-message-ttl': 60000})
        
#         # Bind the queue to the exchange with the routing key
#         self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)
        
#         # Set QoS settings
#         self.channel.basic_qos(prefetch_count=1)

#         # Consume messages from the queue
#         self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False) #True)

#         ## Set expiry period: at queue or publishing? (max amount of time before being removed, would be important)
#         # mq_recieve_thread = threading.Thread(target=self.channel.start_consuming)
#         # mq_recieve_thread.start()

#     def remove_message_callback(self, app_name: str, app_topic: str) -> None:
#         """
#         Removes a message callback for application name and topic `prefix.app_name.app_topic`.

#         Args:
#             app_name (str): The application name
#             app_topic (str): The application topic
#         """
#         self.channel.stop_consuming()

#     def set_wallclock_offset(
#         self, host="pool.ntp.org", retry_delay_s: int = 5, max_retry: int = 5
#     ) -> None:
#         """
#         Issues a Network Time Protocol (NTP) request to determine the system clock offset.

#         Args:
#             host (str): NTP host (default: 'pool.ntp.org')
#             retry_delay_s (int): number of seconds to wait before retrying
#             max_retry (int): maximum number of retries allowed
#         """
#         for i in range(max_retry):
#             try:
#                 logger.info(f"Contacting {host} to retrieve wallclock offset.")
#                 response = ntplib.NTPClient().request(host, version=3, timeout=2)
#                 offset = timedelta(seconds=response.offset)
#                 self.simulator.set_wallclock_offset(offset)
#                 logger.info(f"Wallclock offset updated to {offset}.")
#                 return
#             except ntplib.NTPException:
#                 logger.warn(
#                     f"Could not connect to {host}, attempt #{i+1}/{max_retry} in {retry_delay_s} s."
#                 )
#                 time.sleep(retry_delay_s)
