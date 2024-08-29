from datetime import datetime, timedelta
import logging
import ntplib
import pika
import threading
from typing import Callable
from keycloak.keycloak_openid import KeycloakOpenID
import getpass
import ssl
from keycloak.exceptions import KeycloakAuthenticationError
import time

from .schemas import ReadyStatus
from .simulator import Simulator
from .application_utils import (
    ConnectionConfig,
    TimeStatusPublisher,
    ModeStatusObserver,
    ShutDownObserver,
)

logger = logging.getLogger(__name__)

class Application(object):
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
        self._is_running = False
        # self._is_connected = False #threading.Event()

    # def ready(self) -> None:
    #     status = ReadyStatus.parse_obj(
    #         {
    #             "name": self.app_name,
    #             "description": self.app_description,
    #             "properties": {"ready": True},
    #         }
    #     )

    #     self.channel.basic_publish(
    #         exchange='',
    #         routing_key=f"{self.prefix}.{self.app_name}.status.ready",
    #         body=status.json(by_alias=True, exclude_none=True),
    #     )
    def ready(self) -> None:
        status = ReadyStatus.parse_obj(
            {
                "name": self.app_name,
                "description": self.app_description,
                "properties": {"ready": True},
            }
        )

        routing_key, queue_name = self.declare_bind_queue(app_name=self.app_name, topic='status.ready')
        
        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=routing_key, #f"{self.prefix}.{self.app_name}.status.ready",
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

    def on_connection_error(self, connection, error):
        logger.error(f"Connection error: {error}")
        # self._is_connected.clear()

    def on_connection_closed(self, connection, reason):
        logger.info(f"Connection closed: {reason}")
        # self._is_connected.clear()
        # if not self._should_stop.is_set():
        #     # Try to reconnect if not shutting down
        #     self.start_up(self.prefix, self.connection_parameters)

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
        self._is_running = True

        # Get access token
        access_token, refresh_token = self.new_access_token(config)

        # Set connection parameters
        parameters = pika.ConnectionParameters(
                host=config.host,
                port=config.rabbitmq_port,
                credentials=pika.PlainCredentials('', access_token),
                ssl_options=pika.SSLOptions() if config.is_tls else None,
                heartbeat=600
            )
        
        def on_connection_open(connection):
            self.connection = connection
            self.channel = connection.channel(on_open_callback=self.on_channel_open)
            # self.connection.channel(on_open_callback=self.on_channel_open)
            logger.info("Connection established successfully.")

        # Establish the connection using non-blocking select_connection
        self.connection = pika.SelectConnection(
            parameters=parameters,
            on_open_callback=on_connection_open,
            on_open_error_callback=self.on_connection_error,
            on_close_callback=self.on_connection_closed,
        )

        # Start the I/O loop in a separate thread
        threading.Thread(target=self._start_io_loop).start()

        # Configure observers
        self._create_time_status_publisher(time_status_step, time_status_init)
        self._create_mode_status_observer()
        if shut_down_when_terminated:
            self._create_shut_down_observer()

        logger.info(f"Application {self.app_name} successfully started up.")

    def _start_io_loop(self):
        while self._is_running:
            self.connection.ioloop.start()

    # def on_connection_open(self, connection):
    #     # self.channel = connection.channel(on_open_callback=self.on_channel_open)
    #     self.connection = connection
    #     self.connection.channel(on_open_callback=self.on_channel_open)
    #     logger.info("Connection established successfully.")

    def on_channel_open(self, channel):
        
        # self.channel = channel
        # Signal that connection is established
        # self._is_connected.set()
        # Declare necessary exchanges, queues, and bindings
        # For example: self.channel.exchange_declare(exchange='logs', exchange_type='topic')
        self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # Channel is now open and ready for use
        logger.info("Channel opened and ready.")

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

    def _create_time_status_publisher(
        self, time_status_step: timedelta, time_status_init: datetime
    ) -> None:
        if time_status_step is not None:
            if self._time_status_publisher is not None:
                self.simulator.remove_observer(self._time_status_publisher)
            self._time_status_publisher = TimeStatusPublisher(
                self, time_status_step, time_status_init
            )
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

    def shut_down(self) -> None:
        if self._time_status_publisher is not None:
            self.simulator.remove_observer(self._time_status_publisher)
        self._time_status_publisher = None

        self._is_running = False
        self.connection.ioloop.stop()
        self.connection.close()
        self.prefix = None
        logger.info(f"Application {self.app_name} successfully shut down.")

    def create_routing_key(self, app_name: str, topic: str):
        # routing_key = f"{self.prefix}.{self.app_name}.{topic}"
        routing_key = '.'.join([self.prefix, app_name, topic])
        return routing_key

    def declare_bind_queue(self, app_name: str, topic: str, app_specific_extender: str = None) -> None:
        
        # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        routing_key = self.create_routing_key(app_name=app_name, topic=topic)

        if app_specific_extender:
            queue_name = '.'.join([routing_key, app_specific_extender]) #f"{routing_key}.{app_specific_extender}"

        else: 
            queue_name = routing_key

        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=routing_key)

        logger.debug(f'Bound queue "{queue_name}" to topic "{routing_key}".')

        return routing_key, queue_name

    def send_message(self, app_name, app_topic: str, payload: str, app_specific_extender: str = None) -> None:
        # # Declare topic and queue names
        # topic = f"{self.prefix}.{self.app_name}.{app_topic}"
        # queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        # # Declare a queue and bind it to the exchange with the routing key
        # self.channel.queue_declare(queue=queue_name, durable=True)
        # self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic) #f"{self.prefix}.{self.app_name}.status.time")

        # routing_key, queue_name = self.declare_bind_queue(app_name=self.app_name, topic=app_topic)

        if app_specific_extender:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic, app_specific_extender=app_specific_extender)

        else:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic)

        # Expiration of 60000 ms = 60 sec
        self.channel.basic_publish(
            exchange=self.prefix,
            routing_key=routing_key,
            body=payload,
            properties=pika.BasicProperties(expiration='30000')
        )

        logger.info(f'Successfully sent message "{payload}" to topic "{routing_key}".')

    def add_message_callback(self, app_name: str, app_topic: str, user_callback: Callable, app_specific_extender: str = None):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        # topic = f"{self.prefix}.{app_name}.{app_topic}"
        # queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        combined_cb = self.combined_callback(user_callback)


        # # Declare the exchange
        # # self.channel.exchange_declare(exchange=self.prefix, exchange_type='topic')

        # # # Declare the queue, 60000 milliseconds = 60 seconds 
        # self.channel.queue_declare(queue=queue_name, durable=True) #, arguments={'x-message-ttl': 60000})
        
        # # Bind the queue to the exchange with the routing key
        # self.channel.queue_bind(exchange=self.prefix, queue=queue_name, routing_key=topic)

        if app_specific_extender:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic, app_specific_extender=app_specific_extender)
        else:
            routing_key, queue_name = self.declare_bind_queue(app_name=app_name, topic=app_topic)
        
        # Set QoS settings
        self.channel.basic_qos(prefetch_count=1)

        self._consumer_tag = self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=combined_cb,
            auto_ack=False)
        
        logger.info(f"Subscribing and adding callback to topic: {routing_key}")

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

    # def on_queue_declared(self, callback):
    #     def inner_declare_ok(method_frame):
    #         self.channel.basic_consume(
    #             queue=method_frame.method.queue,
    #             on_message_callback=callback,
    #             auto_ack=True
    #         )
    #     return inner_declare_ok

    def remove_message_callback(self, app_name: str, app_topic: str) -> None:
        topic = f"{self.prefix}.{app_name}.{app_topic}"
        logger.debug(f"Removing callback from topic: {topic}")
        self.channel.queue_delete(queue=topic)

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

    def set_wallclock_offset(
        self, host="pool.ntp.org", retry_delay_s: int = 5, max_retry: int = 5
    ) -> None:
        for i in range(max_retry):
            try:
                logger.info(f"Contacting {host} to retrieve wallclock offset.")
                response = ntplib.NTPClient().request(host, version=3, timeout=2)
                offset = timedelta(seconds=response.offset)
                self.simulator.set_wallclock_offset(offset)
                logger.info(f"Wallclock offset updated to {offset}.")
                return
            except ntplib.NTPException:
                logger.warning(
                    f"Could not connect to {host}, attempt #{i+1}/{max_retry} in {retry_delay_s} s."
                )
                time.sleep(retry_delay_s)
