"""
Code to import, clean, and format NYC school, covid, attendence, broadband,
    and geo data.

This code taken from https://dev.socrata.com/foundry/data.cityofnewyork.us/wg9x-4ke6
https://dev.socrata.com/foundry/data.cityofnewyork.us/vww9-qguh
https://dev.socrata.com/foundry/data.cityofnewyork.us/qz5f-yx82
https://data.cityofnewyork.us/api/geospatial/pri4-ifjk?method=export&format=Shapefile
https://data.cityofnewyork.us/Health/Modified-Zip-Code-Tabulation-Areas-MODZCTA-/pri4-ifjk
https://github.com/nychealth/coronavirus-data/raw/master/trends/caserate-by-modzcta.csv
with syntax guidance from https://github.com/xmunoz/sodapy/blob/master/examples/soql_queries.py

Code References:
https://chrisalbon.com/python/data_wrangling/pandas_lowercase_column_names/
https://geographyplanning.buffalostate.edu/wMix/Python/Geopandas%20Basics%20using%20Open%20Data.html
https://www.w3schools.com/python/python_try_except.asp
https://geopandas.org/gallery/create_geopandas_from_pandas.html
https://www.unix.com/unix-for-dummies-questions-and-answers/157130-move-content-directory-another.html
https://www.geeksforgeeks.org/convert-the-column-type-from-string-to-datetime-format-in-pandas-dataframe/
https://stackoverflow.com/questions/20845213/how-to-avoid-python-pandas-creating-an-index-in-a-saved-csv
https://datascienceparichay.com/article/pandas-fillna-with-values-from-another-column/
"""


import json
import pandas as pd
import requests
from sodapy import Socrata
import sqlite3
import create_table
import re
import geopandas as gpd
import pygeos
import rtree



FILE_TYPES = ['csv', 'json', 'html']

SOURCE_PARAMS = {'data/nyc_schools.csv': 
                    {'data_id': 'wg9x-4ke6',
                    'max_rows': 2500, 
                    'select_cols': ['fiscal_year', 'system_code', 
                                'location_code', 'location_name',
                                'managed_by_name', 'location_type_description',
                                'location_category_description',
                                'primary_building_code', 
                                'primary_address_line_1',
                                'state_code', 'longitude',
                                'latitude', 'census_tract',
                                'borough_block_lot', 'nta',
                                'nta_name'], 
                    'rename_cols': {'managed_by_name': 'managed_by', 
                        'location_type_description': 'location_type',
                        'location_category_description': 'location_category'}},
                'data/nyc_broadband.csv':
                     {'data_id': 'qz5f-yx82',
                    'max_rows': 280, 
                    'select_cols': ['oid', 'zip_code', 
                                    'home_broadband_adoption', 
                                    'mobile_broadband_adoption',
                                    'no_internet_access_percentage', 
                                    'no_home_broadband_adoption', 
                                    'no_mobile_broadband_adoption',
                                    'public_computer_center_count',
                                    'public_wi_fi_count'],
                    'rename_cols': {'no_internet_access_percentage': 
                            'no_internet_access'} 
                    },
                'data/nyc_attendance.csv':
                    {'data_id': 'vww9-qguh',
                    'soql_filter': "year == '2018-19'",
                    'max_rows': 138000, 
                    'rename_cols': 
                        {'chronically_absent_1': 'perc_chronically_absent'}}
                    }

# Import broadband, attendence, and school data with Socrata API
def import_data(data_id, soql_filter=None, max_rows=2000, select_cols=None,
                                            rename_cols=None, out_file=None):
    '''
    Import specified data from data.cityofnewyork.us domain
        using Socrata API; filter for desired columns; rename columns;
        store as csv or json
    
    Inputs:
        data_id (str): string identifier for dataset to append to domain
        soql_filter (str): optional filter string to append to query
        max_rows (int): max rows to pull; must be specified to avoid default
            limit of 1000 placed on unspecified request (defaults to 2000)
        select_cols (list): list of columns from the data to keep (defaults
            to all)
        rename_cols (dict): dictionary mapping original col names to renamed
            columns (defaults to no renames)
        out_file (str): relative file path and filename for output
            (defaults to data/data_id.csv)

    Returns (DataFrame): Pandas DataFrame containing data
    '''

    client = Socrata("data.cityofnewyork.us", None)
    if soql_filter:
        results = client.get(data_id, where=soql_filter, limit=max_rows)
    else:
        results = client.get(data_id, limit=max_rows)
    df = pd.DataFrame.from_records(results)

    if select_cols:
        df = df.loc[:, select_cols]
    if rename_cols:
        df = df.rename(columns=rename_cols)

    if out_file:
        try:
            out_form = re.search(r'.+\.([\w]+)', out_file).groups()[0]
            if not out_form in FILE_TYPES:
                raise Exception("Unsupported file type provided")
        except:
            return "Couldn't interpret output file type"
    else:
        out_file = 'data/' + data_id + '.csv'
        out_form = 'csv'
    
    if out_form == 'csv':
        df.to_csv(out_file, index=False)
    elif out_form == 'json':
        df.to_json(out_file, index=False)
    elif out_form == 'html':
        df.to_html(out_file, index=False)

    return 'Created data file ' + out_file


def create_files(out_files=None):
    '''
    Pull data from NYC Open Data and output to 
        files. Pull specified files only or all files in
        SOURCE_PARAMS dict.
    
    Inputs:
        out_files (list): list of strings identifying files to
            create, corresponding to entries in SOURCE_PARAMS.
            Defaults to all.
    '''

    if not out_files:
        out_files = SOURCE_PARAMS.keys()

    for out_file in out_files:
        print('')
        print('Creating file ', out_file, "...")
        import_data(SOURCE_PARAMS[out_file]['data_id'], 
            soql_filter=SOURCE_PARAMS[out_file].get('soql_filter', None), 
            max_rows=SOURCE_PARAMS[out_file].get('max_rows', None), 
            select_cols=SOURCE_PARAMS[out_file].get('select_cols', None),
            rename_cols=SOURCE_PARAMS[out_file].get('rename_cols', None),
            out_file=out_file)


"""
Run creation of initial files
"""
create_files()


"""
Import geographic shapes for modified zip code tabulation areas (MODZCTA)
"""
print('')
print('Importing modzcta geographic identification...')
modzcta_url = \
    "https://data.cityofnewyork.us/api/geospatial/pri4-ifjk?method=export&format=Shapefile"
modzcta_gdf = gpd.read_file(modzcta_url)
modzcta_gdf = gpd.GeoDataFrame(modzcta_gdf)
modzcta_gdf.to_file('data/nyc_geo/nyc_modzcta.shp')
print('Created data/nyc_geo/nyc_modzcta geo files')


"""
Update NYC schools data to add geo fields
"""
print('')
print('Updating NYC schools data with geographic identifiers...')
schools_df = pd.read_csv("data/nyc_schools.csv")
schools_filt = schools_df[schools_df.loc[:,'longitude']<-1]
schools_gdf = gpd.GeoDataFrame(
    schools_filt, geometry=gpd.points_from_xy(
    schools_filt.longitude, schools_filt.latitude), crs=4326)
schools_geo = gpd.sjoin(schools_gdf, modzcta_gdf, how="left", op='intersects')
schools_geo = schools_geo.drop(['index_right', 'label', \
    'borough_block_lot'], axis=1)
schools_geo.loc[:, 'city'] = 'New York City'
schools_geo.to_file('data/nyc_geo')
print('Created data/nyc_geo/nyc_geo geo files')


"""
Import NYC covid data and rearrange for use
"""
print('')
print("Importing NYC covid case rates...")
covid_cases_url = \
    "https://github.com/nychealth/coronavirus-data/raw/master/trends/caserate-by-modzcta.csv"
covid_cases_df = pd.read_csv(covid_cases_url)

# Identify dates
covid_cases_df.loc[:,'week_dt'] = \
    pd.to_datetime(covid_cases_df.loc[:,'week_ending'],
                format="%m/%d/%Y")
covid_cases_df.loc[:,'month'] = \
    covid_cases_df.loc[:, 'week_dt'].dt.strftime("%m")
covid_cases_df.loc[:,'year'] = \
    covid_cases_df.loc[:, 'week_dt'].dt.strftime("%Y")

# Remove unneeded fields
covid_cases_mo = covid_cases_df.loc[:,'CASERATE_CITY':'year']
covid_cases_mo = covid_cases_mo.drop('week_dt', axis=1)

# Rearrange table by month, year, modzcta
covid_cases_gb = covid_cases_mo.groupby(['month', 'year'])
covid_cases_gb = covid_cases_gb.mean()
covid_cases = pd.DataFrame(covid_cases_gb)
covid_cases = covid_cases.melt(ignore_index=False)

# Clean up tablenames, filter unneeded aggregate records
covid_cases.loc[:,'modzcta'] = \
    covid_cases.loc[:,'variable'].str.extract(r'[\w]+_([\w]+)', expand=False)
covid_cases.rename(columns={'value':'case_rate_100k'}, inplace=True)
covid_cases=covid_cases.drop(['variable'], axis=1)
covid_cases = covid_cases[covid_cases.loc[:,'modzcta'].str.len() > 4]
covid_cases.to_csv('data/nyc_covid.csv')
print('Created file data/nyc_covid.csv')


"""
Roll up NYC broadband to level of MODZCTA:
"""
print('')
print('Rolling up NYC broadband data from zip to modzcta level...')
zcta_modzcta_url = \
    'https://raw.githubusercontent.com/nychealth/coronavirus-data/master/Geography-resources/ZCTA-to-MODZCTA.csv'
broadband_raw = pd.read_csv('data/nyc_broadband.csv')
zcta_df = pd.read_csv(zcta_modzcta_url)
zcta_df = zcta_df.astype('str', copy=False)

# Add back leading 0s removed from some zip codes
broadband_raw['zip_code'] = broadband_raw['zip_code'].astype('str').apply(lambda x: x.zfill(5))

# Merge broadband data with zcta-modzcta mapping
broadband_mod = broadband_raw.merge(zcta_df, how='left', left_on="zip_code", right_on="ZCTA")
values = {'MODZCTA': broadband_mod['zip_code']}
broadband_mod['MODZCTA'].fillna(broadband_mod['zip_code'], inplace=True)
broadband_gb = broadband_mod.groupby('MODZCTA')

# Take grouped by mean for percentage fields
broadband_gb_mean = broadband_gb.mean()
broadband_gb_mean = broadband_gb_mean.loc[:,'home_broadband_adoption':'no_mobile_broadband_adoption']

# Take grouped by sum for count fields
broadband_gb_sum = broadband_gb.sum()
broadband_gb_sum = broadband_gb_sum.loc[:,'public_computer_center_count':'public_wi_fi_count']

# Join sum and mean fields as final broadband table
broadband_modzcta = broadband_gb_mean.join(broadband_gb_sum)
broadband_modzcta.to_csv('data/nyc_broadband.csv')
print('Updated file data/nyc_broadband.csv')


"""
Create non-geographic version of NYC geo files for more performant
    map creation
"""

# Create NYC schools and modzcta files
print('')
print('Creating/updating nyc modzcta and school csvs with string '
    'geo fields from geographic data...')
modzcta_gdf = gpd.read_file('data/nyc_geo/nyc_modzcta.shp')
modzcta_gdf.to_csv('data/nyc_modzcta.csv')
print('Created data/nyc_modzcta.csv')
schools_gdf = gpd.read_file('data/nyc_geo/nyc_geo.shp')
schools_gdf.to_csv('data/nyc_schools.csv')
print('Created data/nyc_schools.csv')
