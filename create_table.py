'''
Create table in SQL database
'''
import sqlite3
import sys
import re
import geopandas
import pandas as pd

DIC_OF_TYPES = {"int64": "INTEGER", "object": "nvarchar", "float64": "REAL",
                "bool": "bit", "datetime64": "datetime"}


def import_data(filename, datatype):
    '''
    Imports data into Pandas DataFrame

    Inputs:
        filename (str): name of file to be imported
        datatype (str): type of file

    Returns:
        Pandas DataFrame
    '''
    if datatype == "csv":
        data = pd.read_csv(filename)
    elif datatype == "json":
        data = pd.read_json(filename, orient="records")
    elif datatype == "geojson":
        data = geopandas.read_file(filename)
    df = pd.DataFrame(data)
    return df


def create_table(filename, unwantedcols=None):
    '''
    Creates the table in the school_access database if none exists

    Inputs:
        filename (str): name of file containing data to be added
        unwantedcols (list): list of column string names that are not to be
            added to the database
    Returns:
        Nothing, adds table to SQL database
    '''
    if unwantedcols is None:
        unwantedcols = []
    parsed_filename = re.search(r'((?:[\w-]+))\.((?:[\w-]+))', filename)
    df = import_data(filename, parsed_filename.group(2)).drop(unwantedcols,
                                                              axis=1)
    connection = sqlite3.connect('school_access.sqlite3')
    c = connection.cursor()
    table_cols = []

    for col in df:
        coltype = DIC_OF_TYPES[str(df[col].dtype)]
        if len(re.findall(r"\d+", col[0])) > 0:
            raise Exception(f"Error: Number starts column {col}, please rename")
        string = col + ' ' + coltype
        table_cols.append(string)
    create_table_str = '''CREATE TABLE IF NOT EXISTS ''' + \
                       parsed_filename.group(1) + ' (' + \
                       ', '.join(table_cols) + ')'
    c.execute(create_table_str)

    question_marks = ", ".join(["?"] * len(df.columns))
    add_row_str = '''INSERT INTO ''' + parsed_filename.group(1) + \
                    ' VALUES (' + question_marks + ')'
    for row in df.itertuples(index=False):
        args = list(row)
        c.execute(add_row_str, args)
    connection.commit()
    connection.close()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        unwanted_cols = sys.argv[2:]
        create_table(sys.argv[1], unwanted_cols)
    elif len(sys.argv) == 2:
        create_table(sys.argv[1])
    else:
        print("Error: file not given")
