'''
Code to create csv files  for search terms
'''

import sqlite3
import csv


def generate_lists():

    connection = sqlite3.connect('../../school_access.sqlite3')
    c = connection.cursor()
    # get lists of unique values from sql database
    neighborhood = c.execute('''SELECT DISTINCT Neighborhood as Community, UPPER(CITY)
                                FROM la_schools 
                                UNION SELECT DISTINCT community, UPPER(city)
                                FROM chicago_schools_with_community 
                                UNION SELECT DISTINCT nta_name, UPPER(city)
                                FROM nyc_schools;''').fetchall()
    city = c.execute('''SELECT DISTINCT UPPER(CITY) 
                        FROM la_schools
                        UNION SELECT DISTINCT UPPER(city)
                        FROM chicago_schools_with_community
                        UNION SELECT DISTINCT UPPER(city)
                        FROM nyc_schools;''').fetchall()
    school = c.execute('''SELECT DISTINCT MPD_NAME as School, UPPER(CITY) 
                        FROM la_schools
                        UNION SELECT DISTINCT long_name, UPPER(city)
                        FROM chicago_schools_with_community
                        UNION SELECT DISTINCT location_name, UPPER(city)
                        FROM nyc_schools;''').fetchall()
    state = c.execute('''SELECT DISTINCT 'CA' as State 
                        FROM la_schools
                        UNION SELECT DISTINCT 'IL'
                        FROM chicago_schools_with_community
                        UNION SELECT DISTINCT state_code
                        FROM nyc_schools;''').fetchall()
    # any other areas we want to be able to input name-wise?

    connection.close()

    # write lists of unique values to file
    f = open('nbhd_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for row in neighborhood:
        w.writerow(row)
    f.close()

    f = open('city_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for row in city:
        w.writerow(row)
    f.close()

    f = open('school_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for row in school:
        w.writerow(row)
    f.close()

    f = open('state_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for row in state:
        w.writerow(row)
    f.close()

'''
Currently we don't need this code, but might be worth keeping around?
'''
# def find_gps(building):

#     connection = sqlite3.connect('../../data/courses_tables.db')
#     c = connection.cursor()

#     loc = c.execute('''SELECT lon, lat FROM gps WHERE building = ?''',
#                     (building,)).fetchone()

#     connection.close()

#     lon = loc[0]
#     lat = loc[1]

#     return (lon, lat)

if __name__ == "__main__":
    generate_lists()