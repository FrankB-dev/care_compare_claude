# care_compare_claude

## Primer
The goal of this respository is to visualize national complications and deaths data using a local, simple dash-plotly app.

The relevant data are organized in folders named by year in the data folder.

Claude Code is expected to write the Python code required and to test it locally.  In the process, Claude is
expected to add and commit changes to this git repository and push it upstream.

A virtual Python environment using libraries in the requirements.txt has already been created and activated.  The
desired implementation will use only these libraries.

Two Python files should be created.
The first Python file should be located in the data folder and should be named 'extract_and_store_data.py'.
It's function is to extract the relevant national complications and deaths data from the folders named by year and to store the data in
a sqlite database called care_compare_db_1 and in a table named complications_and_deaths_national.  In the process, the data should
be cleaned and checked for consistency.  New columns and features can be added if it's believed that it will help visualizaion
later in the dash-plotly app.

The second python file should be named app.py and placed in the src folder.  When executed, this app should start a dash-plotly
app that reads the sqlite complications_and_deats_national table.  The app should allow the user to select a measure that they
wish to view.  After dropdown selection,  over time via a dropdown filte
