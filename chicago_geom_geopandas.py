# script to connect Chicago Public Schools data to their respective community areas
# this code was heavily created with the help of Hana Passen and Charmaine Runes

import geopandas as gpd

def schools_to_community():
    '''
    Reads in chicago community, school, and zipcode data. Filters out unecessary
    columns. Created geodataframes and joins the datasets. Renames columns and
    changes datatypes. Writes out as new csv file.
    '''

    # read in community data
    comm_geo = gpd.read_file("https://data.cityofchicago.org/resource/igwz-8jzy.geojson")

    # read in schools data
    schools_geo = gpd.read_file("https://data.cityofchicago.org/resource/83yd-jxxw.geojson")

    # read in zip geo data
    zip_geo = gpd.read_file("data/Boundaries - ZIP Codes.geojson")


    # filter out some columns
    schools_geo = schools_geo[['school_id', 'short_name', 'long_name', 'address', 'attendance_boundaries', 'geometry', 'zip', 'is_high_school', 'is_middle_school', 'is_elementary_school', 'grades_offered']]
    zip_geo = zip_geo[['zip', 'geometry']]

    # create geodataframes
    schools_geo = gpd.GeoDataFrame(schools_geo,
                                   geometry='geometry',
                                   crs=3435)

    comms_geo = gpd.GeoDataFrame(comm_geo,
                                 geometry='geometry',
                                 crs=3435)

    zip_geo = gpd.GeoDataFrame(zip_geo,
                               geometry='geometry',
                               crs=3435)

    # join the two datasets
    schools_with_comm = gpd.sjoin(schools_geo, comms_geo, how="inner", op="within")
    schools_with_comm = schools_with_comm[['school_id','short_name','long_name','address','attendance_boundaries','geometry','community', 'zip', 'is_high_school', 'is_middle_school', 'is_elementary_school', 'grades_offered']]

    schools_with_comm['city'] = "CHICAGO"

    schools_with_comm = schools_with_comm.merge(zip_geo, on='zip', how='left')

    # rename cols and change dtypes
    schools_with_comm = schools_with_comm.rename(columns={'geometry_x':'school_geometry', 'geometry_y':'zip_geometry'})

    schools_with_comm.loc[:, 'zip'] = schools_with_comm['zip'].astype(int)
    schools_with_comm.loc[:, 'school_id'] = schools_with_comm['school_id'].astype(int)

    # write out csv file
    schools_with_comm.to_csv("data/chicago_schools_with_community.csv")
