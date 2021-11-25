# Hate Crime Project
This was a group project that I built during college. My team and I built a database from a dataset
collected from the FBI and created a simple webpage using Plotly Dash to visualize the data.

## To run this project
1. Make sure that you have the hate crimes database up and running
2. Create a virtual environment and activate it (see [here](https://virtualenv.pypa.io/en/latest/) for more info on virtual environments)
3. Enter the file `main.py` and change the db access string to what it should be for your database (see the section on connect_string [here](https://pythondata.com/quick-tip-sqlalchemy-for-mysql-and-pandas/)). The db access string is located on the first line after `if __name__ == '__main__'` near the bottom of the file.
3. Navigate to this directory and run `pip install -r requirements.txt`
4. Run `python3 main.py`
5. The application should be running at localhost:8050
