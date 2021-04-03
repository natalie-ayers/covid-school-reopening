"""
Create geopandas map for given city with school and covid data.

References:
https://stackoverflow.com/questions/39582984/pandas-merging-on-string-columns-not-working-bug
https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot.html
https://towardsdatascience.com/lets-make-a-map-using-geopandas-pandas-and-matplotlib-to-make-a-chloropleth-map-dddc31c1983d
https://geopandas.org/docs/user_guide/mapping.html
https://stackoverflow.com/questions/3279560/reverse-colormap-in-matplotlib
https://github.com/geopandas/geopandas/issues/603
https://matplotlib.org/stable/tutorials/colors/colormaps.html
https://www.tutorialspoint.com/How-to-use-variables-in-Python-regular-expression
https://www.tutorialspoint.com/apply-uppercase-to-a-column-in-pandas-dataframe-in-python
https://www.geeksforgeeks.org/how-to-change-the-font-size-of-the-title-in-a-matplotlib-figure/
"""

import pandas as pd
from shapely import wkt
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import reopening_guide
import re
import os

CITIES_MAP = {
            'CHICAGO': {
                'viz_var': 'Avg_Monthly_Case_Rate',
                'title': 'Chicago Schools and Covid Rates, ',
                'legend': 'Avg Monthly Covid Rates per 100k',
                'abbr': 'chi'
            },
            'NEW YORK CITY':{
                'viz_var': 'case_rate_100k',
                'title': 'New York City Schools and Covid Rates, ',
                'legend': 'Covid Case Rate per 100k',
                'abbr': 'nyc'
            },
            'LOS ANGELES':{
                'viz_var': 'Covid_Rates',
                'title': 'Los Angeles Schools and Covid Rates, ',
                'legend': 'Covid Case Rate per 100k',
                'abbr': 'la'
            }
            }

COL_DICT = {'neighborhood': 'Community',
            'school': 'Name', 'month': 'Month',
            'grade_level': 'Grade_Level_Cat',
            'city': 'City'}

FIG_FILE = 'static/school_map.png'


def get_schools(args_to_ui):
    '''
    Create schools GeoDataFrame with associated suggested_action 
        categorization, filtered by user inputs from Django interface.

    Inputs:
        args_to_ui (dict): dictionary containing user input filters from Django
            interface. Options for filtering include:
            - city (str): (required)
            - month (str): (required)
            - grade_level (str): (required)
            - school (str): (optional) partial or full school name
            - neighborhood (str): (optional) partial or full neighborhood

    Returns (gdf): a GeoDataFrame containing schools, 
        their locations, and their categorizations
    '''

    city = args_to_ui['city']

    # Create formatted dictionary to use for filters
    filters = {}
    for col, val in args_to_ui.items():
        if col != 'sort_by':
            if col == 'month':
               filters[COL_DICT[col]] = int(val) 
            else:
                filters[COL_DICT[col]] = val.upper()
    
    # Import categorized school table created by reopening_guide.py,
        # filter by user inputs
    cat_df = pd.read_csv('../data/categorized_schools.csv')
    for col, val in filters.items():
        if col in ['Community', 'Name']:
            cat_df = cat_df[cat_df[col].str.extract( \
                            pat='.*(' + val + ').*',expand=False) == val]
        else:
            cat_df = cat_df[cat_df[col] == val]

    cat_df_filt = cat_df.loc[:, ('Name','Suggested_Action')]

    # Depending on the chosen city, import and format school data as df
    if city == 'CHICAGO':
        schools_df = pd.read_csv('../data/chicago_schools_with_community.csv')
        schools_df.rename(columns={'school_geometry': 'geometry', 
            'long_name': 'school_name'}, inplace=True)
        schools_df = schools_df.loc[:,('school_name','geometry')]

    if city == 'NEW YORK CITY':
        schools_df = pd.read_csv('../data/nyc_schools.csv')
        schools_df = schools_df.loc[:,('location_n','location_1','geometry')]
        schools_df.rename(columns={'location_n': 'school_name', 
            'location_1': 'school_type'}, inplace=True)

    if city == 'LOS ANGELES':
        schools_df = pd.read_csv('../data/la_schools.csv')
        schools_df = schools_df.loc[:,('FULLNAME',
                            'MPD_NAME', 'Neighborhood', 'geometry')]
        schools_df.loc[:, 'school_name'] = schools_df['MPD_NAME']

    # Merge school df with categorized df to filter and add categorizations,
        # create schools_gdf to use in final map
    schools_df['school_name'] = schools_df['school_name'].str.upper()
    schools_df = schools_df.merge(cat_df_filt, 
                        left_on = "school_name", right_on = "Name")
    schools_df = schools_df.drop('Name', axis=1)
    schools_df['geometry'] = schools_df['geometry'].apply(wkt.loads)
    schools_gdf = gpd.GeoDataFrame(schools_df)

    return schools_gdf
    

def get_covid_geo(args_to_ui):
    '''
    Create GeoDataFrame containing covid levels for each geographic
        area/neighborhood for the user-selected month

    Inputs:
        args_to_ui (dict): dictionary containing user input filters from Django
            interface. Options for filtering include:
            - city (str): (required)
            - month (str): (required)
            - grade_level (str): (required)
            - school (str): (optional) partial or full school name
            - neighborhood (str): (optional) partial or full neighborhood

    Returns (gdf): a GeoDataFrame containing geographic regions/neighborhoods,
        their geo-polygons, and their covid levels
    '''

    city = args_to_ui['city']
    month = int(args_to_ui['month'])

    # Depending on city, generate gdf for neighborhoods and join
        # to filtered covid data for the city
    if city == 'CHICAGO':
        covid_df = pd.read_csv('../data/chicago_covid_grouped.csv')
        covid_df['ZIP'] = covid_df['ZIP'].astype('str')
        covid_df_mo = covid_df[covid_df['month'] == month]
       
        zip_gdf = gpd.read_file('../data/Boundaries - ZIP Codes.geojson')
        zip_gdf = zip_gdf.loc[:,('zip','geometry')]
        
        covid_gdf = covid_df_mo.merge(zip_gdf, left_on="ZIP", right_on="zip")
        covid_gdf = gpd.GeoDataFrame(covid_gdf)
    
    if city == 'NEW YORK CITY':
        modzcta_df = pd.read_csv('../data/nyc_modzcta.csv')
        modzcta_df = modzcta_df.astype({'modzcta': 'string'})

        covid_df = pd.read_csv('../data/nyc_covid.csv')
        covid_df = covid_df.astype({'modzcta': 'string'})
        covid_df_mo = covid_df[covid_df.loc[:,'month'] == month]

        covid_gdf = modzcta_df.merge(covid_df_mo, left_on="modzcta", right_on="modzcta")
        covid_gdf['geometry'] = covid_gdf['geometry'].apply(wkt.loads)
        covid_gdf = gpd.GeoDataFrame(covid_gdf)

    if city == "LOS ANGELES":
        broadband_df = pd.read_csv('../data/la_broadband.csv')
        broadband_df = broadband_df.loc[:,('Name','geometry')]
        
        covid_df = pd.read_csv('../data/la_covid.csv')
        covid_df_mo = covid_df[covid_df.loc[:,'month'] == month]
        covid_df_mo = covid_df_mo.loc[:,('Community','Covid_Rates')]

        covid_gdf = covid_df_mo.merge(broadband_df, 
                            left_on="Community", right_on="Name")
        covid_gdf = covid_gdf.drop('Name', axis=1)
        covid_gdf['geometry'] = covid_gdf['geometry'].apply(wkt.loads)
        covid_gdf = gpd.GeoDataFrame(covid_gdf)

    return covid_gdf


def create_viz(args_to_ui):
    '''
    Create map of covid rates by zip/neighborhood with schools identified
        by their suggested opening classification. Store map for use by
        ui/query_schools.py in Django interface.

    Inputs:
        args_to_ui (dict): dictionary containing user input filters from Django
            interface. Options for filtering include:
            - city (str): (required)
            - month (str): (required)
            - grade_level (str): (required)
            - school (str): (optional) partial or full school name
            - neighborhood (str): (optional) partial or full neighborhood
    '''

    city = args_to_ui['city']
    month = int(args_to_ui['month'])
    if month >= 4:
        year = 2020
    else:
        year = 2021

    schools_gdf = get_schools(args_to_ui)
    covid_gdf = get_covid_geo(args_to_ui)
    
    viz_var = CITIES_MAP[city]['viz_var']
    pt_var = 'Suggested_Action'
    fig, ax = plt.subplots(figsize=(20, 12))

    base = covid_gdf.plot(column=viz_var, cmap='RdYlBu_r', legend=True,
        ax=ax, legend_kwds={'label': CITIES_MAP[city]['legend'],
                            'orientation': "vertical"})

    schools_gdf.plot(ax=base, marker='o', column=pt_var, 
                cmap='jet', legend=True, markersize=7)
    ax.axis('off')
    title = CITIES_MAP[city]['title'] + str(month) + '/' + str(year)
    ax.set_title(title, fontsize=20)
    
    fig.savefig(FIG_FILE, dpi=300)
