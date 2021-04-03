# script to clean chicago_broadband.csv

import pandas as pd

def clean_broadband():
    '''
    Reads in chicago_broadband.csv. Filters out unneccesary columns.
    Rename columns and reformat percent columns. Writes out as new csv file.
    '''

    chi_broad = pd.read_csv("data/chicago_broadband.csv")

    chi_broad = chi_broad.iloc[:, 2:]

    chi_broad = chi_broad.rename(columns={"Community Area":"community_area",
                                 "# Children without Broadband Internet":"num_children_no_broadband",
                                 "% Children without Broadband Internet":"percent_children_no_broadband",
                                 "# Households without Broadband":"num_households_no_broadband",
                                 "% Households without Broadband":"percent_households_no_broadband"})

    chi_broad['percent_children_no_broadband'] = chi_broad['percent_children_no_broadband'].str.strip('%').astype(float) * 0.01
    chi_broad['percent_households_no_broadband'] = chi_broad['percent_households_no_broadband'].str.strip('%').astype(float) * 0.01

    chi_broad.to_csv("data/chicago_broadband.csv", index=False)
