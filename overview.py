# Imports
import os
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app import app, server
from utils import EnergiAPI

# Globals
UPDATE_INTERVAL = os.environ.get("UPDATE_INTERVAL", 60000)
api = EnergiAPI()

# Styling
colors = {
    'background': '#303030',
    'plot_background': '#adb5bd',
    'text': '#ffffff',
    'infobox': '#888',
    'fossil': '#524e15',
    'solar': '#ded00d',
    'offshore': '#0d79de',
    'onshore': '#04b834'
}


# Graphing

## Production Sources Graph
def prod_graph():
    '''
    Generates the Production and Sources Graph.
    '''

    df = api.sql_to_df("SELECT \"Minutes1DK\", \"Minutes1UTC\", \"ProductionGe100MW\", \"ProductionLt100MW\", \"SolarPower\", \"OffshoreWindPower\", \"OnshoreWindPower\" FROM \"powersystemrightnow\" WHERE \"Minutes1UTC\" >= ((current_timestamp at time zone 'UTC') - INTERVAL '1 day')")

    hovertemp = '<b>Production: </b> %{y:.2f} MWh/h'+'<br>'+'<b>Time: </b> %{x}'

    x = df['Minutes1DK']
    df['ProductionPlant'] = df['ProductionGe100MW'] + df['ProductionLt100MW']

    fig = px.area(df, x=x, y=df['ProductionPlant'])
    fig.update_traces(name='Power Stations', line=dict(color=colors['fossil']), stackgroup='one',
        hoverinfo='y+x', hovertemplate=hovertemp)

    fig.add_scatter(x=x, y=df['SolarPower'], mode='lines', line=dict(color=colors['solar']),
        showlegend=False, name='Solar Power', stackgroup='one',
        hoverinfo='y+x', hovertemplate=hovertemp)

    fig.add_scatter(x=x, y=df['OffshoreWindPower'], mode='lines', line=dict(color=colors['offshore']),
        showlegend=False, name='Offshore Wind Power', stackgroup='one',
        hoverinfo='y+x', hovertemplate=hovertemp)

    fig.add_scatter(x=x, y=df['OnshoreWindPower'], mode='lines', line=dict(color=colors['onshore']),
        showlegend=False, name='Onshore Wind Power', stackgroup='one',
        hoverinfo='y+x', hovertemplate=hovertemp)

    # Top level layout
    fig.update_layout(
        # Colors
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hoverlabel_bgcolor = colors['infobox'],
        # Graph
        title="<b>Current Production with the Sources of Electricity</b>",
        xaxis_title="<b>Time</b>",
        yaxis_title="<b>Production</b> (MWh/h)",
        hovermode = 'x unified'
    )

    # Pie Chart
    values = [df['ProductionPlant'].mean(), df['SolarPower'].mean(),
        df['OffshoreWindPower'].mean(), df['OnshoreWindPower'].mean()]
    names = ['Power Stations', 'Solar Power', 'Offshore Wind Power', 'Onshore Wind Power']
    pie = px.pie(values=values, names=names, color=names, hole=0.3,
        color_discrete_map={'Power Stations': colors['fossil'],
                            'Solar Power': colors['solar'],
                            'Offshore Wind Power': colors['offshore'],
                            'Onshore Wind Power': colors['onshore']})

    pie.update_traces(hoverinfo='label+percent',
    hovertemplate='<b>%{label}: </b> %{value:.2f} MWh/h', textposition='inside', 
        textinfo='percent+label', showlegend=False)
    pie.update_layout(
        # Colors
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hoverlabel_bgcolor = colors['infobox'],
        # Graph
        title='<b>Proportion of Average Production the last 24 hours</b>'
    )

    return fig, pie

## CO2 Emission Figure
def co2_graph():
    '''
    Generates the CO2 Emission and Prognosis Graph.
    '''
    act_df = api.sql_to_df("SELECT \"Minutes1DK\", \"Minutes1UTC\", \"CO2Emission\" FROM \"powersystemrightnow\" WHERE \"Minutes1UTC\" >= ((current_timestamp at time zone 'UTC') - INTERVAL '1 day')")

    prog_df = api.sql_to_df("SELECT \"Minutes5UTC\", \"Minutes5DK\", \"PriceArea\", \"CO2Emission\" FROM \"co2emisprog\" WHERE \"Minutes5UTC\" >= (current_timestamp at time zone 'UTC') AND \"Minutes5UTC\" < ((current_timestamp at time zone 'UTC') %2B INTERVAL '6 hours') AND \"PriceArea\" = 'DK1' ORDER BY \"Minutes5DK\" ")

    hovertemp = '<b>CO2 Emission: </b> %{y:.2f} g/kWh'+'<br>'+'<b>Time: </b> %{x}'

    co2_fig = px.line(act_df, x='Minutes1DK', y='CO2Emission')
    co2_fig.update_traces(name='Actual', hoverinfo='y+x', hovertemplate=hovertemp)

    co2_fig.add_scatter(x=prog_df['Minutes5DK'], y=prog_df['CO2Emission'],
        mode='lines', showlegend=False, name='Prognosis',
        hoverinfo='y+x', hovertemplate=hovertemp)

    co2_fig.update_layout(
        # Colors
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        # Graph
        title="<b> Current CO2 Emission from Production including a forecast for the next 9 hours </b>",
        xaxis_title="<b>Time</b>",
        yaxis_title="<b>CO2 Emission</b> (g/kWh)",
        hovermode = 'x unified',
        hoverlabel_bgcolor = colors['infobox'])

    # CO2 Emission Gauge
    gauge = go.Figure(go.Indicator(
        value = act_df['CO2Emission'].iloc[0],
        delta = {'reference': act_df['CO2Emission'].iloc[1],
            'increasing': {'color': 'red'}, 'decreasing': {'color': 'green'}},
        mode = 'gauge+number+delta',
        title = {'text': '<b>CO2 Emission Intensity from Production (g/kWh)</b>'},
        gauge = {'axis': {'range': [None, 300]},
                'steps': [
                    {'range': [0, 150], 'color': 'green'},
                    {'range': [150, 225], 'color': 'orange'},
                    {'range': [225, 300], 'color': 'red'}],
                'bar': {'color': 'royalblue'},
                }
    ))
    gauge.update_layout(
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    return co2_fig, gauge

## Button Descriptions
src_desc = {
    'waste': 'Electricity production from power plants using Waste as a main fuel.',
    'offshore': 'Electricity production from Offshore Wind Power.',
    'onshore': 'Electricity production from Onshore Wind Power.',
    'solar': 'Electricity production from solar power.',
    'fossil': 'Electricity production from power plants using hard coal, oil or gas as a main fuel.',
    'other': 'Electricity production from biomass, hydro power or other renewable sources.'
}
sources = ['waste', 'offshore', 'onshore', 'solar', 'fossil', 'other']

def popover_desc(btn):
    return dbc.Popover(
        [
            dbc.PopoverHeader(f'{btn.capitalize()}'),
            dbc.PopoverBody(f'{src_desc[btn]}')
        ],
        id=f'popover-{btn}',
        target=f'{btn}-btn',
        placement=btn,
    )



# Layout
layout = html.Div(
    [
        html.Div(
            [
                # Energy Balance
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Dropdown(
                                id='pricearea-dropdown', value='DK',
                                options=[{'label': 'Denmark', 'value': 'DK'},
                                        {'label': 'Jylland & Fyn', 'value': 'DK1'},
                                        {'label': 'Sjælland & Islands', 'value': 'DK2'}],
                                persistence=True, persistence_type='session'
                                ),
                            ], style={'width': '10%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            [
                                dcc.Markdown('**Click for more information.**'),
                                dbc.Button('Waste Fuel', color='#072e1e', id='waste-btn'),
                                dbc.Button('Offshore Wind Power', color=colors['offshore'], id='offshore-btn'),
                                dbc.Button('Onshore Wind Power', color=colors['onshore'],
                                id='onshore-btn'),
                                dbc.Button('Solar Power', color=colors['solar'], id='solar-btn'),
                                dbc.Button('Fossil Fuel', color=colors['fossil'], id='fossil-btn'),
                                dbc.Button('Other Renewables', color='#00f28d', id='other-btn'),
                                *[popover_desc(src) for src in sources]
                            ], style={'width': '90%', 'display': 'inline-block'}
                        ),
                        html.Div([
                                dcc.Graph(
                                    id='bal-graph-1'
                                ),
                            ], style={'width': '100%', 'display': 'inline-block'}
                        ),                       
                    ]
                )
            ]),
        html.Div(
            [
                # Production + CO2 Emission
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    id='prod-graph-1'
                                    ),
                                dcc.Interval(
                                    id='prodgraph-update',
                                    interval=int(UPDATE_INTERVAL),
                                    n_intervals=0,
                                    ),
                            ], style={'align':'center', 'width': '65.3333333333%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            [dcc.Graph(
                                id='prod-pie-1'),
                            ], style={'align':'center', 'width': '34.6666666667%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id='co2emi-gauge-1'
                                ),
                                dcc.Interval(
                                    id='co2gauge-update',
                                    interval=int(UPDATE_INTERVAL),
                                    n_intervals=0,
                                ),
                            ], style={'align':'center', 'width': '34.6666666667%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id='co2emi-graph-1'
                                    ),
                                dcc.Interval(
                                    id='co2graph-update',
                                    interval=int(UPDATE_INTERVAL*5),
                                    n_intervals=0,
                                ),
                            ], style={'align':'center', 'width': '65.3333333333%', 'display': 'inline-block'}
                        ),
                    ],
                ),
            ]
        )
    ]
)

# Production Row
@app.callback(
    Output("prod-graph-1", "figure"),
    [Input("prodgraph-update", "n_intervals")]
)
def upd_prod_graph(interval):
    fig, _ = prod_graph()
    return fig

@app.callback(
    Output("prod-pie-1", 'figure'),
    [Input("prodgraph-update", "n_intervals")]
)
def prod_pie_graph(interval):
    _, pie = prod_graph()
    return pie

# CO2 Emission Row
@app.callback(
    Output('co2emi-gauge-1', 'figure'),
    [Input('co2gauge-update', 'n_intervals')]
)
def upd_co2_gauge(interval):
    _, gauge = co2_graph()
    return gauge

@app.callback(
    Output("co2emi-graph-1", "figure"),
    [Input("co2graph-update", "n_intervals")]
)
def upd_co2_graph(interval):
    fig, _ = co2_graph()
    return fig

# Energy Balance Row
@app.callback(
    Output("bal-graph-1", "figure"),
    [Input('pricearea-dropdown', 'value')]
)
def bal_graph(pricearea):
    '''
    Generates the Balance between Consumption and Production Graph.
    '''
    pd.options.mode.chained_assignment = None  # SettingWithCopyWarning option

    data = api.sql_to_df("SELECT * FROM \"electricitybalancenonv\" WHERE \"HourUTC\" >= ((current_timestamp at time zone 'UTC') - INTERVAL '7 day') ")
    data = data.fillna(0)

    if pricearea == 'DK1':
        df = data[data['PriceArea'] == 'DK1']
        x = df['HourDK']
    elif pricearea == 'DK2':
        df = data[data['PriceArea'] == 'DK2']
        x = df['HourDK']
    else:
        df = data
        df['HourDK'] = pd.to_datetime(df['HourDK'])
        df = df.resample('60 min', on='HourDK').sum()
        x = df.index

    hovertemp = '%{y:.2f} MWh/h'+'<br>'+'<b>Time: </b> %{x}'
    
    df['Fossil Fuel'] = df['FossilGas'] + df['FossilHardCoal'] + df['FossilOil']
    df['Other Renewables'] = df['OtherRenewable'] + df['HydroPower'] + df['Biomass']

    fig = px.bar(df, x=x, y='Other Renewables')
    fig.update_traces(name='Other Renewables', marker=dict(color='#00f28d'),
        hoverinfo='y+x', hovertemplate=hovertemp)
    fig.add_bar(x=x, y=df['Fossil Fuel'], marker=dict(color=colors['fossil']),
        showlegend=True, name='Fossil Fuel',
        hoverinfo='y+x', hovertemplate=hovertemp)
    fig.add_bar(x=x, y=df['SolarPower'], marker=dict(color=colors['solar']),
        showlegend=True, name='Solar Power',
        hoverinfo='y+x', hovertemplate=hovertemp)    
    fig.add_bar(x=x, y=df['OnshoreWindPower'], marker=dict(color=colors['onshore']),
        showlegend=True, name='Onshore Wind Power',
        hoverinfo='y+x', hovertemplate=hovertemp)
    fig.add_bar(x=x, y=df['OffshoreWindPower'], marker=dict(color=colors['offshore']),
        showlegend=True, name='Offshore Wind Power',
        hoverinfo='y+x', hovertemplate=hovertemp)
    fig.add_bar(x=x, y=df['Waste'], marker=dict(color='#072e1e'),
        showlegend=True, name='Waste Fuel',
        hoverinfo='y+x', hovertemplate=hovertemp)

    fig.add_scatter(x=x, y=df['TotalLoad'], mode='markers+lines', line=dict(color='#f29100'),
        showlegend=True, name='Total Consumption', hovertemplate=hovertemp)
    
    fig.update_layout(
        # Colors
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hoverlabel_bgcolor = colors['infobox'],
        # Graph
        title="<b>Energy Balance between Production and Consumption (excl. Exchanges)</b>",
        xaxis_title="<b>Time</b>",
        yaxis_title="<b>MWh/h</b>",
        hovermode='x unified'
    )

    return fig

## Popover
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

for src in sources:
    app.callback(
        Output(f'popover-{src}', 'is_open'),
        [Input(f'{src}-btn', 'n_clicks')],
        [State(f'popover-{src}', 'is_open')],
    )(toggle_popover)
