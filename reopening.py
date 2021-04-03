'''
This file contains the go() function that runs all necessary scripts to
collect the data, build the sqlite database, and open the django interface
Created by: Natalie Ayers, Sabrina Sedovic, Michelle Orden, references
work from tracker.py by Lamont Samuels
'''
import sqlite3
import sys
import re
import runpy
import chicago_covid_clean
import chicago_geom_geopandas
import clean_chi_attendance
import scrape_la_schools
import clean_la_covid_data
import reopening_guide
import convert_la_data
from create_table import create_table

FILENAMES = {"chicago_covid_grouped.csv": None, "la_broadband.csv": ["Unnamed: 0",
             "geometry"], "la_schools.csv": ["Unnamed: 0","geometry"],
             "nyc_broadband.csv": None, "nyc_schools.csv": "Unnamed: 0",
             "LA_Chronic_Absence_Rates.csv": None,
             "LA_Excellent_Attendance.csv": None,
             "chicago_broadband.csv": None, "nyc_covid.csv": None,
             "chicago_schools_with_community.csv": "Unnamed: 0"}

DATA_DIR = "./data/"

MENU = '''
Select Update Option
(1) All Data - NY, Chi, LA, Categorization (est 7-10 min)
(2) All Data except LA  (est 2-4 min)
(3) Just Categorization Data (< 2 min)
(4) Quit
'''
OPTIONS_HANDLER = {
    1: lambda cxt: print("\n--- sit back and relax!---\n"),
    2: lambda cxt: print("\n--- LA isn't that great anyway---\n"),
    3: lambda cxt: print("\n---not wasting any time!---\n")
}

START = 1
END = 4

class DataUpdate:
    '''
    Class that updates data depending on restriction value
    '''
    def __init__(self, delete=True, data=None):
        self.delete=delete
        self.data=None

    def update_data(self):
        '''
        Launches go function using class' data as restriction
        '''
        go(self.data)


def clean_chicago_data():
    '''
    Calls all python scripts that clean Chicago data files.
    '''
    print("Cleaning data for Chicago...")
    chicago_covid_clean.clean()
    chicago_geom_geopandas.schools_to_community()
    clean_chi_attendance.clean_attendance()


def build_db(files):
    '''
    Builds/updates database using the files collected

    Inputs: files (lst): list of filenames to add to database
    Returns: None, updates SQL database school_access.sqlite3
    '''
    print("Creating tables in the sqlite3 database.")
    connection = sqlite3.connect('school_access.sqlite3')
    c = connection.cursor()
    for filename in files:
        parsed_filename = re.search(r'((?:[\w-]+))\.[\w-]+', filename).group(1)
        print(f"Updating {parsed_filename} in SQL database...")
        query1 = "DROP TABLE IF EXISTS " + parsed_filename
        c.execute(query1)
        unwanted_cols = FILENAMES.get(filename, None)
        create_table(DATA_DIR + filename, unwanted_cols)
    print("Table(s) updated")


def go(restriction):
    '''
    Updates data
    Inputs: restriction (int) depending on what user inputs, restricts what
        is updated
    Returns: Nothing, updates data structures
    '''
    if restriction < 3:
        clean_chicago_data()
        runpy.run_path('scrape_ny_schools.py')
        if restriction < 2:
            print("Scraping LA schools and broadband data...")
            scrape_la_schools.go()
            print("Converting LA data into CSV files...")
            convert_la_data.go()
            print("Scraping and cleaning LA Covid data...")
            clean_la_covid_data.go()
        build_db(FILENAMES)
    print("Updating reopening guidelines...")
    reopening_guide.go()
    build_db(["categorized_schools.csv"])


def retrieve_task():
    option = -1
    while True:
        print(MENU)
        option = int(input("Option: "))
        if option >= START and option <= END:
            break
        print(f"Invalid option({option})")
    return option


def main():
    '''
    Launches selection on terminal
    '''
    delete = True
    print(sys.argv)
    if len(sys.argv) == 2:
        if sys.argv[1] == "False":
            delete = False

    cxt = DataUpdate(delete)
    while True:
        option = retrieve_task()
        if option == 4:
            break
        else:
            handler = OPTIONS_HANDLER[option]
            handler(cxt)
            cxt.data = option
            DataUpdate.update_data(cxt)


if __name__ == "__main__":
    main()
