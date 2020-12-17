# Imports
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

# App Connection
from app import app

# Subpages
import overview, mapview, elmarket

#
app.layout = html.Div([
            # Header
        html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            id='energy__header__subtitle',
                            children=dcc.Markdown('&nbsp **Energy System: Denmark** - an explorative journey through the energy data of Denmark'),
                            style ={'font-size': '1.8rem', 'margin-top':'15px', 'text-align':'center'},
                        ),
                    ],
                    className='overview__header__desc',
                )
            ],
            className='overview__header'
        ),
        dcc.Location(id='url', refresh=False),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink('Overview', active=True, className="nav-item nav-link btn", href='/pages/overview')),
                dbc.NavItem(dbc.NavLink('Municipality View', className="nav-item nav-link btn", href='/pages/mapview')),
                dbc.NavItem(dbc.NavLink('Electricity Market', className="nav-item nav-link btn", href='/pages/elmarket'))
            ], id='tabs', className='row tabs', style={'width':'98%','display':'inline-block'}
        ),
        html.Div(id='page-content', children=[]),
        html.Hr(style={'border':' white'}, className='hr')
])

@app.callback(Output('page-content','children'),
    [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/pages/overview':
        return overview.layout
    elif pathname == '/pages/mapview':
        return mapview.layout
    elif pathname == '/pages/elmarket':
        return elmarket.layout
    else:
        return overview.layout

if __name__ == '__main__':
    app.run_server(debug=True)
