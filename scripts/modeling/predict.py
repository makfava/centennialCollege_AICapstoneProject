# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 17:37:08 2026

@author: marco
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def predict_delay(vehicle_type, station, code, line, hour, weekday, df, model, weights_by_code):
    # Normalize inputs
    station = station.strip().upper()
    code = code.strip().upper()
    line = str(line).strip().upper()

    # Encode categorical features based on the dataset
    station_enc = LabelEncoder().fit(df["Station"]).transform([station])[0]
    line_enc = LabelEncoder().fit(df["Line"]).transform([line])[0]
    code_enc = LabelEncoder().fit(df["Code"]).transform([code])[0]
    description_enc = 0  # placeholder if needed later

    # Derived features
    rush_hour = 1 if hour in [7, 8, 9, 16, 17, 18] else 0
    avg_delay = df[(df["Station"] == station) & (df["Code"] == code)]["Station_Code_AvgDelay"].mean()
    count = df[(df["Station"] == station) & (df["Code"] == code)]["Station_Code_Count"].mean()

    # Build feature vector
    X = pd.DataFrame(
        [
            {
                "Station_enc": station_enc,
                "Description_enc": description_enc,
                "Line_enc": line_enc,
                "Code_enc": code_enc,
                "Hour": hour,
                "Weekday": weekday,
                "RushHour": rush_hour,
                "Month": 9,  # placeholder, could be dynamic
                "Season_enc": 0,  # placeholder, could be dynamic
                "IsWeekend": 1 if weekday in [5, 6] else 0,
                "IsHoliday": 0,  # placeholder, could be dynamic
                "Station_Code_AvgDelay": avg_delay,
                "Station_Code_Count": count,
            }
        ]
    )

    # Model prediction
    model_pred = np.expm1(model.predict(X))[0]
    historical_avg = df[(df["Station"] == station) & (df["Code"] == code)]["Min Delay"].mean()

    # Blend with weights
    wm, wh = weights_by_code.get(code, (0.5, 0.5))
    final_pred = wm * model_pred + wh * historical_avg

    # Print details
    print("Prediction request details:")
    print(f"  Vehicle Type: {vehicle_type}")
    print(f"  Station: {station}")
    print(f"  Line: {line}")
    print(f"  Code: {code}")
    print(f"  Hour: {hour}")
    print(f"  Weekday: {weekday}")
    print(f"Predicted delay (model): {model_pred:.2f} minutes")
    print(f"Historical average delay: {historical_avg:.2f} minutes")
    print(f"Final blended prediction: {final_pred:.2f} minutes")

    return final_pred
