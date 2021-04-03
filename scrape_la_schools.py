'''
Scrapes for LAUSD schools and LA broadband

Data taken from LA's API service through ARCGIS
'''
from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, Polygon, Feature
import pandas as pd
import json
import re
import requests
from shapely.geometry import shape

WANTED_SCHOOLS = ['High School', 'Elementary School', 'Middle School']
WHERE_ALL = ["1=1"]
URLS = [(("https://maps.lacity.org/lahub/rest/"
       "services/LAUSD_Schools/MapServer/0/query"), WANTED_SCHOOLS),
       (("https://gis-portal.usc.edu/arcgis/rest/services/C2IG/EduGap_COVID/"
       "MapServer/2/query"), WHERE_ALL)]
FILENAMES = ["data/la_schools.csv", "data/la_broadband.csv"]

def create_parameters(file_type, where_field=WHERE_ALL, wanted_attributes=None,
                      returnGeometry=True):
    '''
    Creates parameters wanted from the API, specifically for possible attributes
    in the 'MPD_DESC' field.

    Inputs:
        file_type (str): type of file wanted in return
        where_field (lst of str): attributes wanted for 'MPD_DESC' field,
          which determines the type of school
        wanted_attributes (list): determines which columns are wanted to return,
          defaults to all if none provided
        returnGeometry (bool): determines whether to return mapping data 
          alongside results, defaulted to True
    Return:
        dictionary of parameters
    '''
    parameters = {}
    parameters['f'] = file_type
    string = ''

    if where_field == WHERE_ALL:
        parameters['where'] = WHERE_ALL[0]
    else:
        for where in where_field:
            string += 'MPD_DESC like ' + "'" + where + "'" " OR "
        parameters['where'] = string[:-4]

    if wanted_attributes is None:
        parameters['outFields'] = '*'
    else:
        parameters['outFields'] = ''
        for attribute in wanted_attributes:
            parameters['outFields'] += str(attribute) + ', '
        parameters['outFields'] = parameters['outFields'][:-2]

    if returnGeometry:
        parameters["returnGeometry"] = 'true'
    else:
        parameters["returnGeometry"] = 'false'

    return parameters


def find_neighborhood(school_data, county_data):
    '''
    Finds the neighborhood each school is in, matching to broadband data

    Inputs:
        county_data (dict): dictionary of broadband data
        school_data (dict): dictionary of school data
    
    Returns:
        Nothing, updates school_data
    '''
    for school in school_data["features"]:
        point = school["geometry"]
        for neighborhood in county_data["features"]:
            polygon = neighborhood["geometry"]
            nbhd_str= neighborhood["properties"]["Name"]
            shorthand = re.search(r'.*--((?:.*))\sPUMA', nbhd_str)
            if shorthand is not None:
                neighborhood["properties"]["Name"] = str(shorthand.group(1))
            if boolean_point_in_polygon(point, polygon):
                school["properties"]["Neighborhood"] = neighborhood \
                                                          ["properties"]["Name"]


def get_information(url, where_param, wanted_attributes=None):
    '''
    calls to the API using parameters specified and converts response
    to a  dictionary
    
    Inputs:
        url (str): url to page containing API
        where_param (lst of str): parameters wanted from request
        wanted_attributes (list): attribute columns wanted from request, default
            to none
    Returns:
        file_data (dict)
    '''
    parameters = create_parameters('geojson', where_param, wanted_attributes)
    response = requests.get(url, params=parameters)
    file_data = json.loads(response.text)
    return file_data


def create_files(urls, filenames):
    '''
    Prepares and creates files for given urls

    Inputs:
        urls (list of str): urls to pages containing API
        filenames (list of str): file names to save files under, in order
            of given urls
    Returns:
        Nothing, creates csv file
    '''
    file_list = []
    for url in urls:
        response = get_information(url[0], url[1])
        file_list.append(response)
    
    find_neighborhood(file_list[0], file_list[1])

    for file_num, file_data in enumerate(file_list):
        file_attempt = {}
        file_info = file_data["features"]
        for ind_info in file_info:
            if file_num == 0:
                name = "MPD_NAME"
            else:
                name = "Name"
            file_attempt[ind_info["properties"][name]] = file_data
        with open(filenames[file_num], "w") as f:
            json.dump(file_attempt, f, indent=None)


def go():
    create_files(URLS, FILENAMES)


if __name__ == "__main__":
    go()
