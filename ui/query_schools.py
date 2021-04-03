'''
Schools search engine: search

Michelle Orden, Sabrina Sedovic, Natalie Ayers
'''

import sqlite3
import os
import sys
sys.path.append("../")
import create_map
import shutil

DATABASE_FILENAME = os.path.join('../school_access.sqlite3')

def query_results(args_from_ui):
    '''
    Takes a dictionary containing search criteria and returns school, community,
    city, grade level, broadband, attendence, covid, and suggested action results.

    Inputs:
        args_from_ui (dict) - arguments passed into django interface
    Returns: 
        header, table (lst, lst) - header is a list of strings of the column
            names for the output table. table is the data to be displayed
            on the django interface table based on args_from_ui.
    '''

    delete_old_image()

    connection = sqlite3.connect(DATABASE_FILENAME)
    c = connection.cursor()

    keys = args_from_ui.keys()
    args = []

    col_dict = {"School Name" : "s.Name", "Community" : "s.Community", "City" : "s.City",
                "Grade Level" : "s.Grade_Level_Cat", "Percent with Broadband" : "s.Percent_Broadband",
                "2019 Attendance Rate" : "s.Attendance", "Monthly Covid Rate" : "s.Covid_Rates",
                "Suggested Action" : "s.Suggested_Action"}

    s = '''
        SELECT s.Name AS "School Name", s.Community, s.City, s.Grade_Level_Cat as "Grade Level",
        s.Percent_Broadband as "Percent with Broadband", s.Attendance AS "2019 Attendance Rate",
        s.Covid_Rates AS "Monthly Covid Rate per 100k", s.Month, s.Year, s.Suggested_Action AS "Suggested Action"
        FROM categorized_schools AS s
        WHERE 
        '''

    if len(keys) == 0:
        s = s.strip("WHERE \n")
    if "school" in keys:
        s += "s.Name LIKE upper('%'||?||'%') AND "
        args.append(args_from_ui['school'])
    if "neighborhood" in keys:
        s += "s.Community LIKE upper('%'||?||'%') AND "
        args.append(args_from_ui['neighborhood'])
    if "city" in keys:
        s += "s.City = ? AND "
        args.append(args_from_ui['city'])
    if "grade_level" in keys:
        s += "s.Grade_Level_Cat = ? AND "
        args.append(args_from_ui['grade_level'])
    if "month" in keys:
        s += "s.Month = ? AND "
        args.append(args_from_ui['month'])

    s = s.strip(" AND ")

    if "sort_by" in keys:
        s += " ORDER BY " + col_dict[args_from_ui['sort_by']] + " DESC"

    table = c.execute(s, args).fetchall()
    header = get_header(c)

    if args_from_ui and args_from_ui['city'] != "NONE":
        create_map.create_viz(args_from_ui)
    else:
        shutil.copyfile("../default_image.png", "static/school_map.png")
        return header, []

    c.close()

    return header, table


def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    header = []

    for i in cursor.description:
        s = i[0]
        if "." in s:
            s = s[s.find(".")+1:]
        header.append(s)

    return header


def delete_old_image():
    '''
    Deletes the old school_map.png file in static/ to make room for new one.
    '''
    if os.path.exists("static/school_map.png"):
        os.remove("static/school_map.png")
