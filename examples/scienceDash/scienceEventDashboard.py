# -*- coding: utf-8 -*-
"""
This application demonstrates how to create a simple dashboard for
visualizing NOS-T data in real time. It subscribes to the
scienceEventPublisher.py application and displays the science utility
separated by location.
"""

import json
import threading

import dash
import pandas as pd
import pika
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import dotenv_values


# Define a callback function to be called when a message is received
def on_message(ch, method, properties, body):
    """
    Callback to process an incoming message and then run the update_fig function.

    Args:
        ch: The channel object.
        method: The method object.
        properties: The properties object.
        body: The message body.
    """
    eventMessage = json.loads(body.decode("utf-8"))
    eventMessage["location"] = eventMessage["latitude"], eventMessage["longitude"]
    eventLOD.append(eventMessage)
    update_fig(n)


def update_fig(n):
    """
    Updates the dashboard when new data is received.

    Args:
        n: The number of intervals that have passed.
    """
    if not eventLOD:  # Check if eventLOD is empty
        # Return the initial figure with empty data but defined columns
        return px.line(
            pd.DataFrame({"time": [], "utility": []}),
            x="time",
            y="utility",
            labels={"time": "time", "utility": "utility (n.d.)"},
            title="Science Event Utility (Waiting for data...)",
        )

    # Create DataFrame from collected events
    df = pd.DataFrame(data=eventLOD)
    fig = px.line(
        df,
        x="time",
        y="utility",
        color="location",
        markers=True,
        labels={"time": "time", "utility": "utility (n.d.)"},
        title="Science Event Utility",
    )
    return fig


def start_consumer():
    """
    Start consuming messages in a separate thread
    """
    channel.start_consuming()


# name guard
if __name__ == "__main__":

    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]

    # Connection parameters
    pika_credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    parameters = pika.ConnectionParameters(
        HOST,
        PORT,
        "/",
        pika_credentials,  # ssl_options=pika.SSLOptions()
    )

    # Establish connection to RabbitMQ
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the exchange
    exchange_name = "nost_example"
    channel.exchange_declare(exchange=exchange_name, exchange_type="topic")

    # Create a queue with a random name
    result = channel.queue_declare("", exclusive=True)
    queue_name = result.method.queue

    # Bind the queue to the exchange with a routing key
    binding_key = "BCtest.AIAA.eventUtility"
    channel.queue_bind(
        exchange=exchange_name, queue=queue_name, routing_key=binding_key
    )

    print(f"Subscribed to {exchange_name} with binding key {binding_key}")

    # Set up the consumer
    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=True
    )

    # initialize df
    df0 = pd.DataFrame()
    latitude = 0
    longitude = 0
    df0["latitude"] = 0
    df0["longitude"] = 0
    df0["time"] = 0
    df0["utility"] = 0
    df0["location"] = (latitude, longitude)
    n = 0
    eventLOD = []

    # Start consuming in a background thread
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()

    app = dash.Dash(__name__)

    # for dashboard plot
    fig = px.line(
        df0,
        x="time",
        y="utility",
        color="location",
        markers=True,
        labels={"time": "time", "utility": "utility (n.d.)"},
        title="Science Event Utility",
    )

    app.layout = html.Div(
        [
            dcc.Graph(id="Utility_Plot", figure=fig),
            dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),
        ]
    )

    app.callback(
        Output("Utility_Plot", "figure"), Input("interval-component", "n_intervals")
    )(update_fig)

    app.run(debug=True)
