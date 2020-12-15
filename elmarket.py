# Imports
import os
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
from utils import EnergiAPI
from app import app, server
from datetime import datetime
from overview import colors

#Globals
api = EnergiAPI()

# Data
elprices = api.sql_to_df("SELECT * FROM \"elspotprices\" WHERE \"HourUTC\" >= ((current_timestamp at time zone 'UTC') - INTERVAL '1 year')")

# Cleaning
def get_el_prices(pricearea):
    pd.options.mode.chained_assignment = None  # SettingWithCopyWarning option

    pa = elprices[elprices['PriceArea'] == f'{pricearea}']
    pa['Day'] = pa['HourDK'].apply(lambda row: datetime.strptime(row[:10], '%Y-%m-%d'))
    pa = pa.sort_values(by='HourDK')

    ls_col = ['Date','Open', 'Close', 'High', 'Low']
    ls = []
    for date in pa['Day'].unique():
        df_ = pa[pa['Day'] == date]
        ls.append([date, df_['SpotPriceEUR'].iloc[0],df_['SpotPriceEUR'].iloc[-1],df_['SpotPriceEUR'].max(),df_['SpotPriceEUR'].min()])
    
    dff = pd.DataFrame(ls, columns=ls_col)

    return dff

dk1_df = get_el_prices('DK1')
dk2_df = get_el_prices('DK2')


# Page Layout
layout = html.Div([
    html.Div([
        html.Span(dcc.Markdown('Electricity Spot Prices.'), style ={'font-size': '1.4rem', 'margin-top':'15px', 'text-align':'center'}),

        html.Div([
            dcc.RadioItems(
                id='crossfilter-pricearea',
                options=[{'label': i, 'value': i} for i in ['DK1', 'DK2']],
                value='DK1'
            ),
        ], style={'display': 'inline-block'}),
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': colors['background'],
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(
            id='candlestick-price'
        ),
    ], style={'width': '100%', 'display': 'inline-block'})
])


@app.callback(
    Output('candlestick-price','figure'),
    [Input('crossfilter-pricearea','value')]
)
def update_candle(pricearea):
    if pricearea == 'DK1':
        df_ = dk1_df
    elif pricearea == 'DK2':
        df_ = dk2_df
    
    fig = go.Figure(data=[go.Candlestick(x=df_['Date'],
        open=df_['Open'],
        high=df_['High'],
        low=df_['Low'],
        close=df_['Close'])])
    
    fig.update_layout(
        # Colors
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hoverlabel_bgcolor = colors['infobox'],
        # Graph
        title="<b>Candlestick Chart of Elspot Prices (€)</b>",
        xaxis_title="<b>Date</b>",
        yaxis_title="<b>€ per MWh</b>",
    )

    return fig