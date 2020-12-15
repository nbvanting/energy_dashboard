# Imports
from dash import Dash
import dash_bootstrap_components as dbc


# App Setup
external_stylesheets = [dbc.themes.DARKLY]
app = Dash(__name__, external_stylesheets=external_stylesheets,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}])

server = app.server

app.config.suppress_callback_exceptions = True
