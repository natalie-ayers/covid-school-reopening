'''
Reopening guide
'''

import sqlite3
import pandas as pd
import numpy as np
from statistics import mode

ALL_COLS = ["Name", "Grade_Level", "Community", "Percent_Broadband",
            "Covid_Rates", "Attendance", "Year", "Month"]
NUMERIC_COLS = ["Percent_Broadband", "Attendance", "Covid_Rates", "year",
                "month"]

GL_DICT = {"HIGH SCHOOL": "HIGH SCHOOL", "ELEMENTARY SCHOOL":
           "ELEMENTARY SCHOOL", "UNKNOWN":"ELEMENTARY SCHOOL", "MIDDLE SCHOOL":
           "MIDDLE SCHOOL","ELEMENTARY": "ELEMENTARY SCHOOL",
           "SECONDARY SCHOOL": "HIGH SCHOOL", "K-8":"MIDDLE SCHOOL",
           "JUNIOR HIGH-INTERMEDIATE-MIDDLE": "MIDDLE SCHOOL",
           "K-12 ALL GRADES": "HIGH SCHOOL","EARLY CHILDHOOD":
           "ELEMENTARY SCHOOL"}
GRADE_CV_SUG = {"HIGH SCHOOL": "VIRTUAL", "ELEMENTARY SCHOOL": "IN-PERSON",
                "MIDDLE SCHOOL": "HYBRID", "UNKNOWN": "HYBRID"}
COVID_DICT = {"LOW": "IN-PERSON", "MODERATE": {"ELEMENTARY SCHOOL": "IN-PERSON",
               "MIDDLE SCHOOL":"HYBRID", "HIGH SCHOOL" :"HYBRID"}, 
              "SUBSTANTIAL": "HYBRID", "HIGH": {"ELEMENTARY SCHOOL": "HYBRID",
               "MIDDLE SCHOOL":"VIRTUAL", "HIGH SCHOOL" :"VIRTUAL"}}
ATTENDANCE_SUG = {"HIGH": "VIRTUAL", "MEDIUM": "HYBRID", "LOW": 
                 {"ELEMENTARY SCHOOL": "IN-PERSON", "MIDDLE SCHOOL": "HYBRID", 
                  "HIGH SCHOOL": "HYBRID", "UNKNOWN": "HYBRID"}}

LA_Q = '''SELECT s.MPD_NAME as Name, s.MPD_DESC as Grade_Level,
          s.Neighborhood as Community, 
          b.Has_PC_and_Broadband as Percent_Broadband,
          c.Covid_Rates as Covid_Rates, (ea.PercentExcellentAttendance - 
          ca.ChronicAbsenceRate) as Attendance, c.year as Year, c.month as Month
          FROM la_schools as s JOIN la_broadband as b JOIN la_covid as c 
          JOIN LA_Chronic_Absence_Rates as ca 
          JOIN LA_Excellent_Attendance as ea ON s.Neighborhood=b.Name 
          AND b.Name=c.Community AND s.CDSCODE = ca.CDSCode
          AND s.CDSCODE = ea.CDSCode
          WHERE NOT (month = 3 AND year = 2020)
          GROUP BY MPD_NAME, year, month;'''

CHI_Q = '''SELECT s.long_name as Name, CASE WHEN 
           s.is_high_school THEN "HIGH SCHOOL"
           WHEN s.is_elementary_school THEN "ELEMENTARY SCHOOL"
           WHEN s.is_middle_school THEN "MIDDLE SCHOOL"
           ELSE "UNKNOWN" END AS Grade_Level, s.community as Community,
           (1 - b.percent_children_no_broadband) as Percent_Broadband,
           c.Avg_Monthly_Case_Rate as Covid_Rates,
           a.attendance_2019 as Attendance, c.month as Month
           FROM chicago_schools_with_community as s 
           JOIN chicago_broadband as b
           JOIN chicago_covid_grouped as c 
           JOIN chicago_attendance_clean as a
           ON s.community = b.community_area AND s.zip=c.ZIP 
           AND s.school_id = a.school_id;'''

NY_Q = '''SELECT s.location_n as Name, 
          s.location_1 as Grade_Level, s.nta_name as Community,
          b.home_broadband_adoption as Percent_Broadband,
          c.case_rate_100k as Covid_Rates,
          a.attendance as Attendance, c.year as Year, c.month as Month
          FROM nyc_schools as s JOIN
          nyc_broadband as b JOIN nyc_covid as c JOIN nyc_attendance as a
          ON s.modzcta=b.MODZCTA
          AND s.modzcta=c.modzcta AND s.system_cod=a.dbn
          GROUP BY Name, month;'''

def collect_requests():
    '''
    Collects the data of the three cities from the SQL database

    Returns: three pandas dataframes, corresponding to LA, Chicago and New York
    City respectively
    '''
    connection = sqlite3.connect("school_access.sqlite3")

    la_data = pd.read_sql_query(LA_Q, connection)
    chi_data = pd.read_sql_query(CHI_Q, connection)
    ny_data = pd.read_sql_query(NY_Q, connection)
    connection.close()

    la_data["City"] = "LOS ANGELES"
    chi_data["City"] = "CHICAGO"
    ny_data["City"] = "NEW YORK CITY"

    return la_data, chi_data, ny_data


def clean_data(data):
    '''
    Cleans data to create uniformity between all three cities and prepare
    for analysis
    Inputs:
        data: Pandas dataframe
    Returns None, updates dataframe
    '''
    for col in ALL_COLS:
        if col not in data.columns and col == "Year":
            data["Year"] = 2020
            data.loc[data["Month"] < 4, "Year"] = 2021
        if data[col].dtype == "object":
            data[col] = data[col].str.upper()
        if col in NUMERIC_COLS and data[col].dtype not in ["int64", "float64"]:
            data[col] = data[col].astype(float)
        if col == "Grade_Level":
            data["Grade_Level_Cat"] = data["Grade_Level"].map(GL_DICT)
        if col == "Attendance" and min(data[col]) < 0:
            data[col] = data[col].apply(lambda x: .5 * (x - 
                                        data[col].min()) / (data[col] \
                                        .max() - data[col].min()) + .5)


def categorize_covid(rate):
    '''
    Categorizes the Covid rate between 4 categories
    Inputs - rate (int) the average weekly covid rate for an area at a given 
                month
    Returns (str) categorical description of rate level
    '''
    if 0 <= rate <= 9:
        return "LOW"
    elif 10 < rate <= 49:
        return "MODERATE"
    elif 49 < rate <= 99:
        return "SUBSTANTIAL"
    return "HIGH"


def categorize_column(df, col_name):
    '''
    Categorizes the data into low, medium and high groupings based on
    normalization
    Inputs:
        df (Pandas Dataframe)
        col_name (str) Column to categorize
    Returns
        None, adds column of the categorization call col_name + "_CAT"
    '''
    info = df[col_name].describe()
    def categorize_column_helper(value):
        if value < info["25%"]:
            return "LOW"
        if value <= info["75%"]:
            return "MEDIUM"
        return "HIGH"
    df[col_name + "_Cat"] = df[col_name].map(categorize_column_helper)


def suggest_broadband(bb_val, grade_level):
    '''
    Suggests action based on broadband value
    Inputs:
        bb_val (float): precentage (in decimal form) of households with 
            broadband in surrounding community
        grade_level (str): grade level of school
    Returns:
        broadband_val(str) Suggested action
    '''
    if bb_val <= .8:
        if grade_level == "ELEMENTARY SCHOOL":
            broadband_val = "IN-PERSON"
        else:
            broadband_val = "HYBRID"
    elif .8 < bb_val < .9:
        broadband_val = "HYBRID"
    else:
        broadband_val = "VIRTUAL"
    return broadband_val


def create_tuple(row):
    '''
    Creates a tuple listing the suggested action in order of each of the
    following: covid suggestion (listed twice as covid transmission should have
    a higher effect in choosing whether to reopen or not), broadband suggestion,
    grade level suggestion and attendance suggestion.
    Inputs: 
        row (Pandas Series): the current school/month combination being 
            checked
    Returns:
        tuple (length 5) of strings, stating either "IN-PERSON", "HYBRID" or
        "VIRTUAL"
    '''
    grade_level = str(row["Grade_Level_Cat"])
    covid_sug = COVID_DICT[row["Covid_Rates_Cat"]]
    if isinstance(covid_sug, dict):
        covid_val = covid_sug[grade_level]
    else:
        covid_val = covid_sug

    broadband_val = suggest_broadband(row["Percent_Broadband"], grade_level)
    grade_level_val = GRADE_CV_SUG[grade_level]

    attend_sug = ATTENDANCE_SUG[row["Attendance_Cat"]]
    if isinstance(attend_sug, dict):
        attend_val = attend_sug[grade_level]
    else:
        attend_val = attend_sug

    return (covid_val, covid_val, broadband_val, grade_level_val, attend_val)


def categorize_all(data):
    '''
    Categorizes all rows in each dataframe to create a suggested action based
    off what is suggested in each suggestion tuple. Also cleans and categorizes
    the data.

    Inputs:
        data (tuple): tuple of dataframes
    
    Returns
        None, updates the dataframe
    '''
    mode_np = np.vectorize(mode)
    for df in data:
        clean_data(df)    
        df["Covid_Rates_Cat"] = df["Covid_Rates"].map(categorize_covid)
        categorize_column(df, "Attendance")
        df["Suggestion_Tuple"] = df.apply(create_tuple, axis=1)
        df["Suggested_Action"] = mode_np(df["Suggestion_Tuple"])
        df.drop("Suggestion_Tuple", axis=1, inplace=True)
        if df.loc[:, "Attendance"].mean() < 1:
            df["Attendance"] = df["Attendance"].apply('{:,.2%}'.format)
        else:
            df["Attendance"] = df["Attendance"].apply('{}%'.format)
        df["Percent_Broadband"] = df["Percent_Broadband"].apply('{:,.2%}'.format)


def go():
    '''
    Creates one large CSV file of the three cities containing necessary columns
    and the final suggested action.
    '''
    (la, chi, ny) = collect_requests()
    categorize_all((la, chi, ny))
    categories = la.append(chi, ignore_index=True).append(ny, ignore_index=True)
    categories.to_csv("data/categorized_schools.csv", index=False)