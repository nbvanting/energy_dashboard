# Imports
from app import app
from utils import EnergiAPI
import json
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from overview import colors

# Globals
api = EnergiAPI()

# Data & Cleaning
## GEOJSON Data File
with open('../dashboard/assets/geo_municipalities.json') as j:
    municipalities = json.load(j)

## Labels
ls = []
for i in range(len(municipalities['features'])):
    ls.append([value for key, value in municipalities['features'][i]['properties'].items() if key == 'lau_1' or key=='label_en'])
labels = pd.DataFrame(ls, columns=['MunicipalityNo', 'Municipality']).drop_duplicates().sort_values(by='MunicipalityNo')
labels = labels.astype(str)

## Mapbox Style Token
with open('../dashboard/assets/token.txt') as f:
    token = f.read()

## Production Data
prod_sources = ['Total Production', 'Onshore Wind Power', 'Offshore Wind Power', 'Solar Power', 'Central Power Plants', 'Decentral Power Plants']
df_prod = api.sql_to_df("SELECT * from \"communityproduction\" WHERE \"Month\" > (CURRENT_DATE - INTERVAL '12 month')")
df_prod.drop(columns=['_full_text', '_id'], inplace=True)
df_prod.rename(columns={'OnshoreWindPower':'Onshore Wind Power', 'OffshoreWindPower':'Offshore Wind Power', \
    'SolarPower':'Solar Power', 'CentralPower':'Central Power Plants', 'DecentralPower':'Decentral Power Plants'}, inplace=True)
df_prod['Month'] = df_prod['Month'].apply(lambda row: row[:7])
df_prod['MunicipalityNo'] = df_prod['MunicipalityNo'].astype(str)
df_prod['Total Production'] = df_prod['Central Power Plants'] + df_prod['Onshore Wind Power'] + \
    df_prod['Offshore Wind Power'] + df_prod['Solar Power'] + df_prod['Decentral Power Plants']
df_prod['Total Production'] = df_prod['Total Production'].round(2)
df_prod = df_prod.merge(labels, on='MunicipalityNo', how='outer')


## Industry Label / Codes
df_indust = api.sql_to_df("SELECT \"ConsumerType_DE35\" as ind_code, \"DE35_UK\" as ind_label FROM \"industrycodes_de35\"")
df_indust.rename(columns={'ind_label':'Industry'}, inplace=True)
industries = df_indust['Industry'].unique().tolist()

## Consumption Data with Industries
df_cons = api.sql_to_df("SELECT * FROM \"consumptionpermunicipalityde35\" WHERE \"Month\" > (CURRENT_DATE - INTERVAL '12 month')")
df_cons.drop(columns=['_id', '_full_text'], inplace=True)
df_cons['Month'] = df_cons['Month'].apply(lambda row: row[:7])
df_cons.rename(columns={'Industrycode_DE35':'ind_code'}, inplace=True)
df_cons['MunicipalityNo'] = df_cons['MunicipalityNo'].astype(str)
df_cons['Total Consumption'] = df_cons['TotalCon'] / 1000 # kwh to mwh
df_cons['Total Consumption'] = df_cons['Total Consumption'].round(2)
df_cons['Consumption per Measurement Point'] = df_cons['TotalCon'] / df_cons['MeasurementPoints']
df_cons = df_cons.merge(df_indust, on='ind_code', how='outer')
df_cons = df_cons.merge(labels, on='MunicipalityNo', how='outer')
mun_codes = df_cons['ind_code'].astype(str).unique().tolist()


# Page Layout
layout = html.Div([
    # Production Row
    html.Div([
        html.Span(dcc.Markdown('Production divided by each Municipality.'), style ={'font-size': '1.4rem', 'margin-top':'15px', 'text-align':'center'}),

        html.Div([
            dcc.RadioItems(
                id='crossfilter-sources',
                options=[{'label': i, 'value': i} for i in prod_sources],
                value=prod_sources[0]
            ),
        ], style={'display': 'inline-block'}),
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': colors['background'],
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(
            id='mapview-prod'
        )
    ], style={'width': '100%', 'display': 'inline-block'}),

    html.Div(dcc.Slider(
        id='crossfilter-month-prod--slider',
        min=1,
        max=12,
        value=11,
        marks={str(month): str(month) for month in df_prod['Month'].unique()},
        step=None
    ), style={'width': '100%'}),

    html.Hr(),
    # Consumption Row
    
    html.Div([
        html.Span(dcc.Markdown('Consumption divided by each Municipality and Industry.'), style ={'font-size': '1.4rem', 'margin-top':'15px', 'text-align':'center'}),
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': colors['background'],
        'padding': '10px 5px'}),

    html.Div([

        dcc.Graph(
            id='mapview-cons',
            style={'width':'49vw','height':'100vh'}
        )
    ], style={'width': '49%', 'height':'100%', 'display': 'inline-block'}),

    html.Div([
        dcc.Graph(id='industries-bar-chart', style={'width':'49vw','height':'100vh'}),
    ], style={'display': 'inline-block', 'width': '49%', 'height':'100%'}),

    html.Div(dcc.Slider(
        id='crossfilter-month-cons--slider',
        min=1,
        max=12,
        value=11,
        marks={str(month): str(month) for month in df_cons['Month'].unique()},
        step=None
    ), style={'width': '60%'})
])


# Callbacks
@app.callback(
    Output('mapview-prod', 'figure'),
    [Input('crossfilter-sources', 'value'),
    Input('crossfilter-month-prod--slider', 'value')]
)
def update_prod_map(source, month_value):

    df_ = df_prod[df_prod['Month'] == f'2020-{month_value}']
    df_ = df_[['Month', 'Municipality', f'{source}']]
    fig = px.choropleth_mapbox(df_, geojson=municipalities, locations='Municipality',
        featureidkey='properties.label_en', color=f'{source}', color_continuous_scale='teal',
        range_color=(df_[f'{source}'].min(), df_[f'{source}'].max()),
        center={'lat': 56.087814, 'lon': 11.780559}, zoom=5.5,
        title='Production per Municipality',
        labels={f'{source}': f'{source}'})

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0}, mapbox_style='mapbox://styles/nbvanting/ckionk34c4y7x17qvx8dusod8',
        mapbox_accesstoken=token,
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],)

    return fig

@app.callback(
    Output('mapview-cons', 'figure'),
    [Input('crossfilter-month-cons--slider', 'value')]
)
def update_cons_map(month_value):

    df_ = df_cons[df_cons['Month'] == f'2020-{month_value}']
    df_ = df_.groupby(by=['Municipality']).agg({'Total Consumption': 'sum'}).reset_index()

    fig = px.choropleth_mapbox(df_, geojson=municipalities, locations='Municipality',
        featureidkey='properties.label_en', color='Total Consumption', color_continuous_scale='teal',
        range_color=(df_['Total Consumption'].min(), df_['Total Consumption'].max()),
        center={'lat': 56.087814, 'lon': 11.780559}, zoom=6,
        title='Consumption per Municipality',
        labels={'Total Consumption': 'Total Consumption'})
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0}, mapbox_style='mapbox://styles/nbvanting/ckionk34c4y7x17qvx8dusod8',
        mapbox_accesstoken=token,
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],)

    return fig

def industry_bar(df, title):

    fig = px.bar(df, x='Industry', y='Total Consumption', barmode='group',
        hover_data=['Industry', 'Total Consumption'],
        color='Total Consumption', 
        color_continuous_scale='teal')
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
    )
    fig.add_annotation(x=0, y=0.9, xanchor='left', yanchor='bottom',
                    xref='paper', yref='paper', showarrow=False, align='left', text=title)

    return fig

@app.callback(
    Output('industries-bar-chart', 'figure'),
    [Input('crossfilter-month-cons--slider', 'value'),
    ]
)
def update_bar(month_value):
    df_ = df_cons[df_cons['Month'] == f'2020-{month_value}']
    df_ = df_.groupby(by=['Industry']).agg({'Total Consumption':'sum'}).reset_index()
    title = f'<b>Consumption per Industry for 2020-{month_value}</b>'

    return industry_bar(df_, title)
