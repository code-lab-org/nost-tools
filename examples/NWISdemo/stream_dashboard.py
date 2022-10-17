# -*- coding: utf-8 -*-
"""
This application uses a callback function to check the .csv file created by
the get_stream_data.py application and then visualize the data with the dash
library. First, the .csv is read into the application, then the dash layout
is set up. The interval component in the dash layout determines how often the
.csv file is checked for new data. Whenever new data is added to the .csv
file, the dash figure is updated.
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

if __name__ == "__main__":

    filename = "gage_height_for_viz.csv"

    plotData = pd.read_csv(filename)
    df = pd.DataFrame(data=plotData, index=[0])

    # for dashboard plot
    fig = px.line(df, x='Request_Time', y='Gage_Height', color='Site_Name', markers=True,
                      labels={"Request_Time":"Request Time", "Gage_Height":"Gage Height (ft)"},
                      title='NWIS Gage Heights')

    app.layout = html.Div([
        dcc.Graph(
            id='Flow_Rate_Plot', figure=fig
            ),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,
            n_intervals=0
        )
    ])

    @app.callback(
        Output('Flow_Rate_Plot', 'figure'),
        [Input("interval-component", 'n_intervals')]
    )

    def update_fig(n):
        plotData = pd.read_csv(filename)
        dffig = pd.DataFrame(data=plotData)
        fig = px.line(dffig, x='Request_Time', y='Gage_Height', color='Site_Name', markers=True,
                          labels={"Request_Time":"Request Time", "Gage_Height":"Gage Height (ft)"},
                          title='NWIS Gage Heights')
        return fig

    if __name__ == '__main__':
        app.run_server(debug=True)
