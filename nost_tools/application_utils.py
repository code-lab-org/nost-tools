"""
Provides utility classes to help applications interact with the broker.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
import pika

from .observer import Observer
from .publisher import ScenarioTimeIntervalPublisher
from .schemas import ModeStatus, TimeStatus
from .simulator import Mode, Simulator

if TYPE_CHECKING:
    from .application import Application

logger = logging.getLogger(__name__)


class ConnectionConfig(object):
    """Connection configuration.

    The configuration settings to establish a connection to the broker, including authentication for the
    user and identification of the server.

    Attributes:
        username (str): client username, provided by NOS-T operator
        password (str): client password, provided by NOS-T operator
        host (str): broker hostname
        port (int): broker port number
        is_tls (bool): True, if the connection uses TLS (Transport Layer Security)
    """

    def __init__(
        self, username: str, password: str, host: str, rabbitmq_port: int, keycloak_port: int, client_id: str, client_secret_key: str, virtual_host: str, is_tls: bool = True
    ):
        """
        Initializes a new connection configuration.

        Args:
            username (str): client username
            password (str): client password
            host (str): broker hostname
            port (int): broker port number
            client_id (str): Keycloak client ID
            client_secret_key (str): Keycloak client secret key
            is_tls (bool): True, if the connection uses Transport Layer Security
        """
        self.username = username
        self.password = password
        self.host = host
        self.rabbitmq_port = rabbitmq_port
        self.keycloak_port = keycloak_port
        self.client_id = client_id
        self.client_secret_key = client_secret_key
        self.virtual_host = virtual_host
        self.is_tls = is_tls


class ShutDownObserver(Observer):
    """
    Observer that shuts down an application after scenario termination.

    Attributes:
        app (:obj:`Application`): application to be shut down after termination
    """

    def __init__(self, app: Application):
        """
        Initializes a new shut down observer.

        Args:
            app (:obj:`Application`): application to be shut down after termination
        """
        self.app = app

    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Shuts down the application in response to a transition to the TERMINATED mode.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE and new_value == Mode.TERMINATED:
            self.app.shut_down()


class TimeStatusPublisher(ScenarioTimeIntervalPublisher):
    """
    Publishes time status messages for an application at a regular interval.

    Attributes:
        app (:obj:`Application`): application to publish time status messages
    """

    def publish_message(self) -> None:
        """
        Publishes a time status message.
        """
        status = TimeStatus.parse_obj(
            {
                "name": self.app.app_name,
                "description": self.app.app_description,
                "properties": {
                    "simTime": self.app.simulator.get_time(),
                    "time": self.app.simulator.get_wallclock_time(),
                },
            }
        )
        logger.info(
            f"Sending time status {status.json(by_alias=True,exclude_none=True)}."
        )
        # publish time status message
        # self.app.client.publish(
        #     f"{self.app.prefix}/{self.app.app_name}/status/time",
        #     status.json(by_alias=True, exclude_none=True),
        # )
        topic = f"{self.app.prefix}.{self.app.app_name}.status.time"
        queue_name = topic #".".join(topic.split(".") + ["queue"]) 

        # Declare the topic exchange
        # self.app.channel.exchange_declare(exchange=self.app.prefix, exchange_type='topic')
        
        # Declare a queue and bind it to the exchange with the routing key
        self.app.channel.queue_declare(queue=queue_name, durable=True)
        self.app.channel.queue_bind(exchange=self.app.prefix, queue=queue_name, routing_key=topic)

        self.app.channel.basic_publish(
            exchange=self.app.prefix,
            routing_key=topic,
            body=status.json(by_alias=True, exclude_none=True),
            properties=pika.BasicProperties(expiration='30000')
        )


class ModeStatusObserver(Observer):
    """
    Observer that publishes mode status messages for an application.

    Attributes:
        app (:obj:`Application`): application to publish mode status messages
    """

    def __init__(self, app: Application):
        """
        Initializes a new mode status observer.
        """
        self.app = app

    # def on_change(
    #     self, source: object, property_name: str, old_value: object, new_value: object
    # ) -> None:
    #     """
    #     Publishes a mode status message in response ot a mode transition.

    #     Args:
    #         source (object): observable that triggered the change
    #         property_name (str): name of the changed property
    #         old_value (obj): old value of the named property
    #         new_value (obj): new value of the named property
    #     """
    #     if property_name == Simulator.PROPERTY_MODE:
    #         status = ModeStatus.parse_obj(
    #             {
    #                 "name": self.app.app_name,
    #                 "description": self.app.app_description,
    #                 "properties": {"mode": self.app.simulator.get_mode()},
    #             }
    #         )
    #         logger.info(
    #             f"Sending mode status {status.json(by_alias=True,exclude_none=True)}."
    #         )
    #         # self.app.client.publish(
    #         #     f"{self.app.prefix}/{self.app.app_name}/status/mode",
    #         #     status.json(by_alias=True, exclude_none=True),
    #         # )

    #         self.app.channel.basic_publish(
    #             exchange=self.app.prefix,
    #             routing_key=f"{self.app.prefix}.{self.app.app_name}.status.mode",
    #             body=status.json(by_alias=True, exclude_none=True)
    #         )
    def on_change(
        self, source: object, property_name: str, old_value: object, new_value: object
    ) -> None:
        """
        Publishes a mode status message in response to a mode transition.

        Args:
            source (object): observable that triggered the change
            property_name (str): name of the changed property
            old_value (obj): old value of the named property
            new_value (obj): new value of the named property
        """
        if property_name == Simulator.PROPERTY_MODE:
            status = ModeStatus.parse_obj(
                {
                    "name": self.app.app_name,
                    "description": self.app.app_description,
                    "properties": {"mode": self.app.simulator.get_mode()},
                }
            )
            logger.info(
                f"Sending mode status {status.json(by_alias=True, exclude_none=True)}."
            )

            # Ensure self.app.prefix is a string
            if not isinstance(self.app.prefix, str):
                raise ValueError(f"Exchange ({self.app.prefix}) must be a string")

            topic = f"{self.app.prefix}.{self.app.app_name}.status.mode"
            queue_name = topic #".".join(topic.split(".") + ["queue"]) 

            # Declare the topic exchange
            # self.app.channel.exchange_declare(exchange=self.app.prefix, exchange_type='topic')
            
            # Declare a queue and bind it to the exchange with the routing key
            self.app.channel.queue_declare(queue=queue_name, durable=True)
            self.app.channel.queue_bind(exchange=self.app.prefix, queue=queue_name, routing_key=topic)

            self.app.channel.basic_publish(
                exchange=self.app.prefix,
                routing_key=topic,
                body=status.json(by_alias=True, exclude_none=True),
                properties=pika.BasicProperties(expiration='30000')
            )
            # logger.info(
            #     f"SENT mode status {status.json(by_alias=True, exclude_none=True)}."
            # )

