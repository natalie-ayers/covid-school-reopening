'''
Scrapes, cleans and connects LA covid data to LA broadband data

LA Covid Data taken from LA Times' Git Hub
'''

import requests
import csv
import io
import geopandas
import pandas as pd
from shapely import wkt

URL1 = "https://raw.githubusercontent.com/datadesk/california-coronavirus" + \
       "-data/master/latimes-place-totals.csv"
URL2 = "https://raw.githubusercontent.com/datadesk/california-coronavirus" + \
       "-data/master/latimes-place-polygons.geojson"

LA_BROADBAND = pd.read_csv("data/la_broadband.csv") \
                        .loc[:,['Name','geometry']]
COL_DROP = ["fips_x", "fips_y", "id_x", "id_y", "county_y", "note", "geometry",
            "centroid_x", "centroid_y", "index_right", "population_y"]


def grab_csv(url):
    '''
    Retrieves csv file from web and transforms into Pandas Dataframe

    Inputs:
        url (str): url where csv file is
    
    Returns Pandas Dataframe
    '''
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"Unable to access site {r.status_code}")
    csv_data = r.content
    data = pd.read_csv(io.StringIO(csv_data.decode('utf-8')))
    return data


def merge_data(df):
    geo = geopandas.read_file(URL2)
    df_w_geo = geo.merge(df, on="name")
    df_bb = geopandas.GeoDataFrame(LA_BROADBAND)
    df_bb["geometry"] = df_bb["geometry"].apply(wkt.loads)
    df_bb.crs = "EPSG:4326"
    final_df = geopandas.sjoin(df_w_geo, df_bb)

    final_df.drop(COL_DROP, axis=1, inplace=True)
    final_df = final_df[~final_df.index.duplicated()]
    return pd.DataFrame(final_df)


def clean_data(df):
    '''
    Cleans data to be used in SQL table

    Inputs:
        df (Pandas dataframe): dataframe containing information on CA covid
            cases
    Returns:
        nothing, converts and saves Pandas dataframe as csv file
    '''
    final_df = merge_data(df)
    final_df.rename(columns={"name": "Neighborhood", "Name": "Community",
                     "county_x": "county", "population_x": "Population"},
                     inplace=True)
    final_df["date"] = pd.to_datetime(final_df["date"], 
                                      infer_datetime_format=True)
    final_df["year"], final_df["month"] = (final_df["date"].dt.year,
                                           final_df["date"].dt.month)
    final_df = final_df.loc[final_df["county"] == "Los Angeles"] \
                       .loc[final_df["Population"] > 0].drop(["county",
                        "zcta_id", "date"], axis=1)

    final_df = final_df.groupby([final_df["Neighborhood"], final_df["year"], 
                                 final_df["month"], final_df["Population"],
                                 final_df["Community"]]) \
                       .first().diff().fillna(0).reset_index()
    final_df["Covid_Rates"] = round((final_df["confirmed_cases"] * 100000 / (
                                     final_df["Population"] * 7)))
    final_df["Covid_Rates"] = final_df["Covid_Rates"] \
                                      .mask(final_df["Covid_Rates"] < 0,0) \
                                      .mask(final_df["Covid_Rates"] > 1000, 
                                            1000)
    final_df.to_csv("data/la_covid.csv", index=False)


def go():
    data = grab_csv(URL1)
    clean_data(data)


if __name__ == "__main__":
    go()