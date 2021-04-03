'''
Converts LA geojson data into csv for quicker conversions later on
'''
import pandas as pd
import geopandas as gpd

LA_SCHOOLS = 'data/la_schools.geojson'
LA_BROADBAND = 'data/la_broadband.geojson'

def go():
    broadband_gdf = gpd.read_file(LA_BROADBAND)
    schools_gdf = gpd.read_file(LA_SCHOOLS)
    schools_gdf.to_csv('data/la_schools.csv')
    school_neighborhoods = schools_gdf['Neighborhood'].unique()
    broadband_filt = broadband_gdf[broadband_gdf.loc[:,'Name'] \
                                  .isin(school_neighborhoods)]
    broadband_filt.to_csv('data/la_broadband.csv')


if __name__ == "__main__":
    go()
