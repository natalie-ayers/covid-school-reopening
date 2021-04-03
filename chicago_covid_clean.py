# scipt to group chicago_covid.csv data by zip and month

import pandas as pd
from datetime import datetime

def clean():
    '''
    Reads in chicago_covid.csv file. Groups data by month and zipcode.
    Filters out unknown zipcodes. Writes out as new csv file.
    '''

    chi_cov = pd.read_csv("data/chicago_covid.csv")

    chi_cov['Week_Start'] = pd.to_datetime(chi_cov['Week_Start'])

    chi_cov['month'] = chi_cov['Week_Start'].dt.strftime("%m")

    chi_cov = chi_cov[chi_cov['ZIP'] != "Unknown"]

    chi_cov.loc[:, 'ZIP'] = chi_cov['ZIP'].astype(int)

    grouped_chi_cov = chi_cov['Case_Rate_Weekly'].groupby(by=[chi_cov['month'], chi_cov['ZIP']]).mean()

    grouped_chi_cov.to_csv("data/chicago_covid_grouped.csv", header=['Avg_Monthly_Case_Rate'])
