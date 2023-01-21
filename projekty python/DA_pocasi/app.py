#import standardních modulů
import copy
import json
import time

#import modulů, které se musí doinstalovat
import requests
import dash
from dash import Dash, Input, Output, dcc, html, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.graph_objects as go
from decouple import config

#načtení konfigurační údajů z config souboru
USERNAME = config('USER')
KEY = config('USER_KEY')

#URL pro API využívaných služeb
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather?"
FORECAST_API_URL = "http://api.openweathermap.org/data/2.5/forecast"
GEO_API_URL_DIRECT = "http://api.openweathermap.org/geo/1.0/direct"
GEO_API_URL_REVERSE = "http://api.openweathermap.org/geo/1.0/reverse"

#
BASE_PARAMS = {"APPID": KEY}


def get_json(_url, params):
    """
    Funkce požádá API službu na dané url o požadavek na základě zadaných parametrů a vrátí odpověď v JSON formátu.

    Vstupy:
        _url: str -> adresa odkazující na API webové služby
        params: Dict[str, str] -> parametry potrebné pro webovou službu

    Návratové hodnoty:
        json -> odpověď služby ve formátu JSONu
    """
    response = requests.get(_url, params)
    return json.loads(response.content)


def get_location_data(url, params, init_coord):
    """
    Funkce přijme adresu API služby, parametry a již explicitně zadané souřadnice. Pokud jsou souřadnice zadané, tak je vrátí v jednotném formátu zpět z funkce. Pokud nejsou, tak požádá službu o jejich získání.

    Vstupy:
        url: str ->
        params: Dict[str, str] ->
        init_coord: ->

    Návratové hodnoty:
        name: str -> 
        lat_lon: ... -> 
    """
    loc_data = get_json(url, params)
    loc_data = loc_data[0]
    if init_coord:
        lat_lon = [params["lat"], params["lon"]]
    else:
        lat_lon = [loc_data["lat"], loc_data["lon"]]
    name = loc_data["name"] + ", " + loc_data["country"]
    return [name, lat_lon]

#
def geocode_forward(query):
    params = BASE_PARAMS.copy()
    params["limit"] = 1
    params["q"] = str(query)
    return get_location_data(GEO_API_URL_DIRECT, params, False)

#
def geocode_reverse(coords):
    params = BASE_PARAMS.copy()
    params["limit"] = 1
    params["lat"], params["lon"] = coords[0], coords[1]
    return get_location_data(GEO_API_URL_REVERSE, params, True)

#
def get_weather(url, coords):
    params = BASE_PARAMS.copy()
    params["lat"], params["lon"] = coords[0], coords[1]
    return get_json(url, params)

#
def generate_weather_card(weather_data):
    temp_feels_like = f'{round(weather_data["main"]["feels_like"] - 273.15, 1)} °C'
    temp_actual = f'{round(weather_data["main"]["temp"] - 273.15, 1)} °C'
    windspeed = f'{round(weather_data["wind"]["speed"]*3.6, 1)} km/h'

    if "gust" in weather_data["wind"].keys():
        windgust = f'{round(weather_data["wind"]["gust"]*3.6, 1)} km/h'
    else:
        windgust = "N/A"

    pressure = f'{weather_data["main"]["pressure"]} hPa'
    humidity = f'{weather_data["main"]["humidity"]} %'

    contents = {
        "Temperature": [(temp_feels_like, "Feels like"),
                        (temp_actual, "Actual")],
        "Wind": [(windspeed, "Wind speed"), (windgust, "Wind gusts")],
        "Atmosphere": [(pressure, "Pressure"), (humidity, "Humidity")]
    }
    card_style = {"width": "6cm", "height": "7cm", "text-align": "center"}

    cards = []

    for key in contents.keys():
        card = dbc.Card([
            dbc.CardHeader(key, className="fw-bold fs-3"),
            dbc.CardBody([
                html.H2(contents[key][0][0],
                        className="card-text fw-bolder text-secondary"),
                html.P(contents[key][0][1],
                       className="card-text fw-bold fs-5"),
                html.H2(contents[key][1][0],
                        className="card-text fw-bolder text-secondary"),
                html.P(contents[key][1][1], className="card-text fw-bold fs-5")
            ],
                style={"font-size": "18px"})
        ],
            class_name="align-self-center",
            style=card_style)
        cards.append(card)

    return dbc.CardGroup(cards)

#
def make_figs(figs):
    return [
        dbc.Row([
            dbc.Col([
                html.H4("Temperature",
                        style={"text-align": "center"},
                        className="mb-2 text-white"),
                dcc.Graph(figure=figs[0], className="m-4 mt-3")
            ],
                width=6),
            dbc.Col([
                html.H4("Wind",
                        style={"text-align": "center"},
                        className="mb-2 text-white"),
                dcc.Graph(figure=figs[1], className="m-4 mt-3")
            ],
                width=6)
        ],
            justify="evenly"),
        dbc.Row([
            dbc.Col([
                html.H4("Pressure",
                        style={"text-align": "center"},
                        className="mb-2 text-white"),
                dcc.Graph(figure=figs[2], className="m-4 mt-3")
            ],
                width=6),
            dbc.Col([
                html.H4("Humidity",
                        style={"text-align": "center"},
                        className="mb-2 text-white"),
                dcc.Graph(figure=figs[3], className="m-4 mt-3")
            ],
                width=6)
        ],
            justify="evenly")
    ]

#
def generate_figures(data):
    tmrw_figs = []
    week_figs = []
    tz = float(data["city"]["timezone"])
    loc_time = time.time() + tz
    tmrw = time.gmtime(loc_time + 86400.0).tm_mday
    curr_time = time.gmtime(loc_time)
    val_dict = {
        "dt": ["Date and time"],
        "temp": ["Temperature", "°C"],
        "wind": ["Wind", "km/h"],
        "press": ["Pressure", "hPa"],
        "hum": ["Humidity", "%"]
    }
    tm_dict = {}
    for dict in data["list"]:
        if time.gmtime(dict["dt"] + tz).tm_mday != curr_time.tm_mday:
            val_dict["dt"].append(
                time.strftime("%d %b %H:%M", time.gmtime(dict["dt"] + tz)))
            val_dict["temp"].append(round(dict["main"]["temp"] - 273.15, 2))
            val_dict["wind"].append(round(dict["wind"]["speed"] * 3.6, 2))
            val_dict["hum"].append(dict["main"]["humidity"])
            val_dict["press"].append(dict["main"]["pressure"])
            if time.gmtime(dict["dt"] + tz).tm_mday == tmrw:
                tm_dict = copy.deepcopy(val_dict)

    for key in val_dict.keys():
        if key == "dt":
            pass
        else:
            tmrw_fig, week_fig = go.Figure(), go.Figure()
            tmrw_fig.add_trace(
                go.Scatter(x=tm_dict["dt"][1:],
                           y=tm_dict[key][2:],
                           name=tm_dict[key][0]))
            tmrw_fig.update_layout(xaxis_title=tm_dict["dt"][0],
                                   yaxis_title=tm_dict[key][1])

            tmrw_figs.append(tmrw_fig)

            week_fig.add_trace(
                go.Scatter(x=val_dict["dt"][1:],
                           y=val_dict[key][2:],
                           name=val_dict[key][0]))
            week_fig.update_layout(xaxis_title=val_dict["dt"][0],
                                   yaxis_title=val_dict[key][1],
                                   autosize=True)
            week_figs.append(week_fig)

    return make_figs(tmrw_figs), make_figs(week_figs)

#přidej do datového dashboardu navigační lištu
navbar = dbc.Navbar(dbc.Container([
    html.A(dbc.Row([
        dbc.Col([html.I(className="bi bi-cloud-sun fs-1", id="my_icon")]),
        dbc.Col([
            dbc.NavbarBrand("My Weather App", class_name="ms-3 fs-3 fw-bold")
        ]),
    ],
        align="center",
        justify="end",
        className="g-0"),
        href="https://openweathermap.org/api",
        style={
        "textDecoration": "none",
        "color": "inherit"
    }),
    dbc.DropdownMenu(
        label="Preferences",
        children=[
            dbc.DropdownMenuItem(html.H5("Display theme"), header=True),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                "Light", active=True, id="lightmode", n_clicks=1),
            dbc.DropdownMenuItem("Dark", id="darkmode", n_clicks=0)
        ],
        in_navbar=True,
        nav=True,
        menu_variant="light",
        id="modemenu",
        toggle_class_name="fs-5 fw-bold")
],
    fluid=True),
    color="white",
    dark=False,
    class_name="m-2",
    id="navbar")


def layout() -> dbc.Container:
    """
    Funkce vytvoří základní rozvržení datového dashboardu

    Návratové hodnoty:
        dbc.Container -> obsahuje vytvořený html-dash layout, který se vykreslí do webové stránky
    """
    return dbc.Container([

        #umístění stránky na vybraný koncový bod Flasku
        dcc.Location(id='url', pathname="/home", refresh=False),
        
        #
        dcc.Store(id="forecast_figs"),
        
        #vytvoření navigační lišty
        dbc.Row([dbc.Col([navbar], width=12)], justify="center"),
        
        #vytvoření informační části datového dashboardu
        html.Div(children=[

            #vytvoření řádku v layoutu, kde bude navigační vyhledávací liště
            dbc.Row([
                #vytvoření vyhledávací lišty
                dbc.Col([
                    dbc.Input(
                        type="text",
                        id="address_bar",
                        placeholder="Search a place (City, Country code)",
                        debounce=True,
                        style={
                            "width": "15cm",
                            'border-radius': '20px'
                        },
                        class_name="m-4 mb-2")
                ], width=5),
                #vytvoření sloupce, kde se objeví zadané město a informace o zataženosti/jasnosti/pršení atd.
                dbc.Col([
                    html.Div([
                        html.P(children=[],
                               id='location_name',
                               className="mt-4 text-white fw-bold fs-3"),
                        html.Div(id="wicon", className="mt-1"),
                        html.P(id="situation",
                               className="mt-4 text-white fw-bold fs-3")
                    ],
                        className="d-flex justify-content-center")
                ], width={"size": 7, "offset": 0})
            ], class_name="g-0", align="center"),
            
            #vytvoření řádku, kde bude interaktivní mapa a tabulka s informacemi o teplotě/větrnosti/atmosféře
            dbc.Row([
                #sloupec s interkativní mapou
                dbc.Col([
                    dl.Map([dl.TileLayer(),
                            dl.LayerGroup(id="layer")],
                           id="map",
                           center=[47, 13],
                           zoom=0.8,
                           style={
                               "width": "15cm",
                               "height": "7cm",
                               "border-radius": "20px"
                    },
                        className="m-4")
                ], width=5),
                #sloupec, kde je původně návodný text a po zadání místa se tam objeví tabulka s informacemi
                dbc.Col([
                    html.Div(html.H1("Select a location to display data",
                                     style={
                                         "text-align": "center",
                                         "color": "white"
                                     }),
                             id="weather_main",
                             className="m-4")
                ],
                    width={"size": 7})
            ], align="center"),
            
            #řádek, kde se bude nacházet dělící čára <hr>
            dbc.Row([
                dbc.Col([
                    html.Hr(style={
                        "border": "2px solid white",
                        "border-radius": "20px",
                        "opacity": "1"
                    }, className="ms-4 me-4")
                    ], width=12)
                ], justify="center"),

            #část dashboardu, kde se objeví výběr délky předpovědy počasí
            html.Div([
                #nadpisový řádek
                dbc.Row([
                    dbc.Col([
                        html.H1(
                            "Forecast",
                            className="text-white",
                            style={"text-align": "center"})
                        ], width=12)
                    ]),
                #řádek s výběrem předpovědi na zítra nebo na následujících 5 dní
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(
                            id="forecast_freq",
                            value="Tomorrow",
                            options=["Tomorrow", "Next 5 days"],
                            clearable=False,
                            className="mt-2 mb-2"
                            )
                        ], width=2)
                    ], justify="center")
                ], id="forecast_descr", hidden=True),

            #část dashboardu, která se přepíše předpovědí po zadání města
            html.Div(
                html.H2(
                    "Select a location to show forecast",
                    style={
                        "text-align": "center",
                        "color": "white",
                        "margin": "15px 0px 20px 0px"
                        }),
                    id="figures")
        
            ],style={
                "border-radius": "20px",
                "padding": "5px"},
            className="ms-4 me-4 min-vh-100 bg-primary")
        ], fluid=True, id="main")


app = Dash("My Weather App",
           external_stylesheets=[
               dbc.themes.BOOTSTRAP, 
               dbc.icons.BOOTSTRAP,
               dbc.icons.FONT_AWESOME
           ],
           suppress_callback_exceptions=True,
           meta_tags=[{
               'name': 'viewport',
               'content': 'width=device-width, initial-scale=1.0'
           }])

#
app.layout = layout

#callback funkce ...
#vstupem je ...
#výstupem je ...
@app.callback([
    Output("layer", "children"),
    Output("map", "center"),
    Output("map", "zoom"),
    Output("address_bar", "value"),
    Output('location_name', 'children'),
], [Input("map", "click_lat_lng"),
    Input("address_bar", "value")],
    prevent_initial_call=True)
def address_to_coordinate(click_lat_lng, search_location):
    zoom = 10
    if dash.ctx.triggered_id == "address_bar":
        name, lat_lon = geocode_forward(search_location)

    elif dash.ctx.triggered_id == "map":
        name, lat_lon = geocode_reverse(click_lat_lng)

    return [
        dl.Marker(position=lat_lon,
                  children=dl.Tooltip("({:.3f}, {:.3f})".format(*lat_lon)))
    ], lat_lon, zoom, name, name

#callback funkce ...
#vstupem je ...
#výstupem je ...
@app.callback([
    Output("weather_main", "children"),
    Output("wicon", "children"),
    Output("situation", "children")
    ], 
    [State("map", "center"),
    Input("location_name", "children")
    ],
    prevent_initial_call=True)
def parse_weather_content(lat_lon, lname):
    weather_data = get_weather(WEATHER_API_URL, lat_lon)
    cards = generate_weather_card(weather_data)
    return [
        cards,
        html.Img(
            src=f'http://openweathermap.org/img/wn/{weather_data["weather"][0]["icon"]}@2x.png',
            style={"height": "2cm"}),
        weather_data["weather"][0]["description"].capitalize()
    ]

#callback funkce ...
#vstupem je ...
#výstupem je ...
@app.callback(
    Output("url", "search"), 
    Input("location_name", "children"))
def update_url(locname):
    if locname == []:
        return ""
    else:
        return f"?loc={locname}"

#callback funkce ...
#vstupem je ...
#výstupem je ...
@app.callback(
    [Output("forecast_figs", "data"),
     Output("forecast_descr", "hidden")],
    [State("map", "center"),
     Input("location_name", "children")],
    prevent_initial_call=True)
def generate_figs(lat_lon, loc):
    forecast = get_weather(FORECAST_API_URL, lat_lon)
    figs = generate_figures(forecast)
    fig_data = {"tomorrow": figs[0], "5days": figs[1]}
    return fig_data, False

#callback funkce pro vykreslení grafu
#vstupem je 
#výstupem je
@app.callback(
    [Output("figures", "children")],
    [Input("forecast_figs", "data"),
     Input("forecast_freq", "value")],
    prevent_initial_call=True)
def display_figs(data, val):
    if val == "Tomorrow":
        return [data["tomorrow"]]
    elif val == "Next 5 days":
        return [data["5days"]]

#callback funkce pro změnu grafického tématu dashboardu na světlé
#vstupem je celé číslo, představující pravdivostní hodnotu, které z tlačítek v preferences bylo zmáčknuté
#výstupem je sada atributů potřebných k nastavení prvků dashboardu na světlé nebo temné schéma
@app.callback([
    Output("navbar", "color"),
    Output("navbar", "dark"),
    Output("modemenu", "menu_variant"),
    Output("modemenu", "toggle_style"),
    Output("lightmode", "active"),
    Output("darkmode", "active"),
    Output("main", "style"),
    Output("my_icon", "style")
], [Input("lightmode", "n_clicks"),
    Input("darkmode", "n_clicks")])
def light_theme(n_light, n_dark):
    #pokud je hodnota n_light = 1 a n_dark = 0, tak nastav potřebné parametry pro světlé téma
    if n_light > n_dark:
        return "white", False, "light", {
            "color": "black"
        }, True, False, {
            "background": "white",
        }, {
            "color": "black"
        }
    #v opačném případě vrať hodnoty stylů a příznaků pro zapnutí temného tématu
    else:
        return "black", True, "dark", {
            "color": "white"
        }, False, True, {
            "background": "black"
        }, {
            "color": "white"
        }


if __name__ == "__main__":
    app.run_server(debug=True)
