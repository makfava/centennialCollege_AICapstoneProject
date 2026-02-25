# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 17:34:49 2026

@author: marco
"""


# preprocessing.py
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import holidays


def preprocess_df(df):
    # Normalize text
    df["Station"] = df["Station"].astype(str).str.strip().str.upper()
    df["Line"] = df["Line"].astype(str).str.strip().str.upper()
    df["Code"] = df["Code"].astype(str).str.strip().str.upper()
    df["Description"] = df["Description"].astype(str).str.strip().str.upper()

    # Fill missing delays by group median
    df["Min Delay"] = df.groupby(["Line", "Station"])["Min Delay"].transform(lambda x: x.fillna(x.median()))
    df["Min Gap"] = df.groupby(["Line", "Station"])["Min Gap"].transform(lambda x: x.fillna(x.median()))
    df = df.dropna(subset=["Min Delay"])

    # Group features
    df["Station_Code_AvgDelay"] = df.groupby(["Station", "Code"])["Min Delay"].transform("mean")
    df["Station_Code_Count"] = df.groupby(["Station", "Code"])["Min Delay"].transform("count")

    # Encode categorical
    df["Station_enc"] = LabelEncoder().fit_transform(df["Station"])
    df["Description_enc"] = LabelEncoder().fit_transform(df["Description"])
    df["Line_enc"] = LabelEncoder().fit_transform(df["Line"])
    df["Code_enc"] = LabelEncoder().fit_transform(df["Code"])

    # Datetime features
    # df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")

    # Ensure Date and Time are parsed
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.time

    # Build Datetime safely
    df["Datetime"] = pd.to_datetime(df["Date"].dt.strftime("%Y-%m-%d") + " " + df["Time"].astype(str), errors="coerce")
    df["Hour"] = df["Datetime"].dt.hour.fillna(-1)
    df["Weekday"] = df["Datetime"].dt.weekday.fillna(-1)
    df["RushHour"] = df["Hour"].apply(lambda h: 1 if h in [7, 8, 9, 16, 17, 18] else 0)
    df["Month"] = df["Datetime"].dt.month.fillna(-1)
    df["Season"] = (
        df["Month"]
        .map(
            {
                12: "Winter",
                1: "Winter",
                2: "Winter",
                3: "Spring",
                4: "Spring",
                5: "Spring",
                6: "Summer",
                7: "Summer",
                8: "Summer",
                9: "Fall",
                10: "Fall",
                11: "Fall",
            }
        )
        .fillna("Unknown")
    )
    df["Season_enc"] = LabelEncoder().fit_transform(df["Season"])
    df["IsWeekend"] = df["Weekday"].apply(lambda d: 1 if d in [5, 6] else 0)

    # Holidays
    years = df["Datetime"].dt.year.dropna().unique().astype(int)
    ca_holidays = holidays.Canada(years=years)
    df["IsHoliday"] = df["Datetime"].dt.date.apply(lambda d: 1 if pd.notnull(d) and d in ca_holidays else 0)

    return df
