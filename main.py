import pandas as pd
import sqlalchemy as sql
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from urllib.request import urlopen
import plotly.graph_objects as go
import json
import us


class DbHelper():
  @classmethod
  def setup(cls, connect_string):
    cls.connect_string = connect_string
    cls.engine = sql.create_engine(connect_string)

  @classmethod
  def query_db(cls, query):
    return pd.read_sql_query(query, cls.engine)

  @classmethod
  def heat_map_query_generator(cls, start_year, end_year, bias):
    '''
    Note: Bias can be left "blank" by specifying "All". Start year and
    end year must be specified.
    '''

    if bias == "All":
      return f"SELECT State, COUNT(Incident_id) FROM CRIME, LOCATION WHERE YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id GROUP BY State ORDER BY COUNT(Incident_id) DESC;"
    return f"SELECT State, COUNT(Incident_id) FROM CRIME, LOCATION WHERE CRIME.Bias LIKE '%%{bias}%%' AND YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id GROUP BY State ORDER BY COUNT(Incident_id) DESC;"

  @classmethod
  def time_series_query_generator(cls, start_year, end_year, bias, state):
    '''
    Note: Bias and state can be left "blank" by specifying "All". Start year and
    end year must be specified.
    '''

    if bias == "All" and state == "All":
      return f"SELECT YEAR(Incident_date) AS Year, COUNT(Incident_id) AS Incident_count FROM CRIME, LOCATION WHERE YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id GROUP BY YEAR(Incident_date);"
    if bias == "All":
      return f"SELECT YEAR(Incident_date) AS Year, COUNT(Incident_id) AS Incident_count FROM CRIME, LOCATION WHERE YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id AND LOCATION.State = '{state}' GROUP BY YEAR(Incident_date);"
    if state == "All":
      return f"SELECT YEAR(Incident_date) AS Year, COUNT(Incident_id) AS Incident_count FROM CRIME, LOCATION WHERE CRIME.Bias LIKE '%%{bias}%%' AND YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id GROUP BY YEAR(Incident_date);"
    return f"SELECT YEAR(Incident_date) AS Year, COUNT(Incident_id) AS Incident_count FROM CRIME, LOCATION WHERE CRIME.Bias LIKE '%%{bias}%%' AND YEAR(Incident_date) BETWEEN {start_year} AND {end_year} AND CRIME.Location_id = LOCATION.Location_id AND LOCATION.State = '{state}' GROUP BY YEAR(Incident_date);"


class PageHelper():

  @classmethod
  def setup(cls):
    cls.possible_years_df = DbHelper.query_db(f"SELECT DISTINCT YEAR(Incident_date) as Incident_year FROM CRIME ORDER BY Incident_year ASC;")
    cls.possible_years_df.columns = ['Year']
    cls.years_list = cls.possible_years_df['Year']

    cls.possible_biases_df = DbHelper.query_db(f"SELECT DISTINCT Bias FROM CRIME ORDER BY Bias ASC;")
    cls.possible_biases_df.columns = ['Bias']
    cls.biases_list = cls.parse_biases(cls.possible_biases_df['Bias'])
    cls.biases_list.insert(0, 'All')

    cls.possible_states_df = DbHelper.query_db(f"SELECT DISTINCT State FROM LOCATION ORDER BY State ASC;")
    cls.possible_states_df.columns = ['State']
    cls.states_list = list(cls.possible_states_df['State'])
    cls.states_list.insert(0, 'All')

    cls.start_year = cls.years_list[0]
    cls.end_year = list(cls.years_list)[-1]
    cls.bias =  cls.biases_list[0]
    cls.state = cls.states_list[0]

    cls.map_query = DbHelper.heat_map_query_generator(start_year=cls.start_year, end_year=cls.end_year, bias=cls.bias)
    cls.time_series_query = DbHelper.time_series_query_generator(start_year=cls.start_year, end_year=cls.end_year, bias=cls.bias, state=cls.state)

  @classmethod
  def parse_biases(cls, bias_list):
    return_list = []
    for line in bias_list:
      bias_array = line.split(";")
      for bias in bias_array:
        if bias not in return_list:
          return_list.append(bias)
    return return_list


  @classmethod
  def create_page(cls):

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    cls.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    child_array = [
      html.H1(children="Hate Crimes in the U.S."),

      html.Div(children='''
          Visualizations of hate crime data from across the United States.
      '''),

      html.Div(children=[
        dcc.Dropdown(
          id='beginning-year-heat-map',
          options=[{'label': year, 'value': year} for year in cls.years_list],
          value=cls.start_year,
          clearable=False
        ),
        dcc.Dropdown(
          id='ending-year-heat-map',
          options=[{'label': year, 'value': year} for year in cls.years_list],
          value=cls.end_year,
          clearable=False
        ),
        dcc.Dropdown(
          id='bias-heat-map',
          options=[{'label': bias, 'value': bias} for bias in cls.biases_list],
          value=cls.bias,
          clearable=False
        )
      ]),

      html.Div(children=
          dcc.Graph(id='heat-map', figure=cls.create_map_fig(cls.map_query))
      ),

      html.Div(children=[
        dcc.Dropdown(
          id='beginning-year-time-series',
          options=[{'label': year, 'value': year} for year in cls.years_list],
          value=cls.start_year,
          clearable=False
        ),
        dcc.Dropdown(
          id='ending-year-time-series',
          options=[{'label': year, 'value': year} for year in cls.years_list],
          value=cls.end_year,
          clearable=False
        ),
        dcc.Dropdown(
          id='state-time-series',
          options=[{'label': state, 'value': state} for state in cls.states_list],
          value=cls.state,
          clearable=False
        ),
        dcc.Dropdown(
          id='bias-time-series',
          options=[{'label': bias, 'value': bias} for bias in cls.biases_list],
          value=cls.bias,
          clearable=False
        )
      ]),

      html.Div(children=
          dcc.Graph(id='time-series', figure=cls.create_time_series_fig(cls.time_series_query))
      ),
    ]

    cls.app.layout = html.Div(children=child_array)

    @cls.app.callback(
      Output("heat-map", 'figure'),
      [
        Input('beginning-year-heat-map', 'value'),
        Input('ending-year-heat-map', 'value'),
        Input('bias-heat-map', 'value')
      ]
    )
    def update_heat_map(start_year, end_year, bias):
      query = DbHelper.heat_map_query_generator(start_year=start_year, end_year=end_year, bias=bias)
      return cls.create_map_fig(query)

    @cls.app.callback(
      Output('time-series', 'figure'),
      [
        Input('beginning-year-time-series', 'value'),
        Input('ending-year-time-series', 'value'),
        Input('bias-time-series', 'value'),
        Input('state-time-series', 'value')
      ]
    )
    def update_time_series(start_year, end_year, bias, state):
      query = DbHelper.time_series_query_generator(start_year=start_year, end_year=end_year, state=state, bias=bias)
      return cls.create_time_series_fig(query)

    return cls.app

  @classmethod
  def create_map_fig(cls, query):
    with urlopen('https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json') as response:
      states = json.load(response)

    df = DbHelper.query_db(query)
    df.columns = ['state', 'num_incidents']
    state_names = df.state
    state_names = cls.clean_state_names(state_names)
    state_fips = [us.states.lookup(state).fips for state in state_names if True]
    df.state = state_fips

    fig = go.Figure(go.Choroplethmapbox(geojson=states, locations=df['state'], z=df['num_incidents'], colorscale="Viridis", zmin=df['num_incidents'].min(), zmax=df['num_incidents'].max(), marker_opacity=0.5, marker_line_width=0))
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

  @classmethod
  def create_time_series_fig(cls, query):
    df = DbHelper.query_db(query)
    df.columns = ['year', 'incident_count']
    fig = go.Figure([go.Bar(x=df['year'], y=df['incident_count'])])
    return fig

  @classmethod
  def clean_state_names(cls, state_names):
    clean_names = []
    clean_names_object = {
      "NewHampshire": "New Hampshire", 
      "NewJersey": "New Jersey", 
      "NewYork": "New York", 
      "NewMexico": "New Mexico", 
      "NorthCarolina": "North Carolina", 
      "NorthDakota": "North Dakota", 
      "RhodeIsland": "Rhode Island", 
      "SouthCarolina": "South Carolina", 
      "SouthDakota": "South Dakota", 
      "WestVirginia": "West Virginia",
      "DistrictofColumbia": "District of Columbia"
    }

    for state_name in state_names:
      if state_name in clean_names_object.keys():
        cleaned_state_name = clean_names_object[state_name]
        clean_names.append(cleaned_state_name)
      else:
        clean_names.append(state_name)

    return clean_names 


if __name__ == '__main__':
  DbHelper.setup('mysql://dgray:@localhost/HATE_CRIME')
  PageHelper.setup()
  app = PageHelper.create_page()
  app.run_server(debug=True)