# script to clean the original metrics_attendance_2019.xls file

import pandas as pd

def clean_attendance():
    '''
    Reads in Chicago attendance data from 2019. Filters out unnecessary columns.
    Renames columns and changes datatypes. Writes out as new csv file.
    '''

    all_metrics = pd.read_excel("data/metrics_attendance_2019.xls", sheet_name="Overtime")

    filtered_2019 = all_metrics.iloc[:, [0, 1, 2, 3, 4, -1]]

    filtered_2019 = filtered_2019[filtered_2019['Group'] == "All (Excludes Pre-K)"]

    filtered_2019 = filtered_2019.rename(columns={"School ID":"school_id",
                                                  "School Name": "school",
                                                  "Group":"group_name",
                                                  2019:"attendance_2019"})

    filtered_2019 = filtered_2019.drop(columns=["Grade"])

    filtered_2019 = filtered_2019[filtered_2019["Network"] != "Charter"]
    filtered_2019 = filtered_2019.drop(columns=["Network"])

    filtered_2019.dropna(subset=['school_id'], inplace=True)

    filtered_2019['school_id'] = filtered_2019['school_id'].astype(int)

    filtered_2019.to_csv("data/chicago_attendance_clean.csv")
