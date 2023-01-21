from dash import Dash, Input, Output, dcc, html, State, callback
import dash

app = Dash("MyApp", external_stylesheets=["""sem patří CSS styly"""],
           meta_tags=[{'name': 'viewport',
                       'content': 'width=device-width, initial-scale=1.0'}])

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),
    dcc.Input(id="myInput", placeholder="My first input"),
    html.Div(id="myOutputDiv")
])

@app.callback(Output("myOutputDiv", "children"), Input("myInput","value"), prevent_initial_call=True)
def update_my_div(value):
    return "Můj vstup: " + value + " v Divu"

if __name__ == "__main__":
    app.run_server(debug=True)