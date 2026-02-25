# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 17:36:44 2026

@author: marco
"""

# train_model.py
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


def train_model(df):
    features = [
        "Station_enc",
        "Description_enc",
        "Line_enc",
        "Code_enc",
        "Hour",
        "Weekday",
        "RushHour",
        "Month",
        "Season_enc",
        "IsWeekend",
        "IsHoliday",
        "Station_Code_AvgDelay",
        "Station_Code_Count",
    ]

    X = df[features].fillna(0)
    y_raw = df["Min Delay"].clip(lower=0)
    y = np.log1p(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train)

    y_pred = np.expm1(model.predict(X_test))
    y_true = np.expm1(y_test)

    print("RMSE:", np.sqrt(mean_squared_error(y_true, y_pred)))
    print("R²:", r2_score(y_true, y_pred))

    return model, features


def compute_weights(df, model, features):
    weights_by_code = {}
    for code in df["Code"].unique():
        df_code = df[df["Code"] == code]
        if len(df_code) < 30:
            continue

        X_code = df_code[features].fillna(0)
        y_code = np.log1p(df_code["Min Delay"].clip(lower=0))

        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_code, y_code, test_size=0.2, random_state=42)

        y_pred_c = model.predict(X_test_c)
        r2_c = r2_score(y_test_c, y_pred_c)

        if r2_c < 0.2:
            wm, wh = 0.3, 0.7
        elif r2_c < 0.5:
            wm, wh = 0.5, 0.5
        else:
            wm, wh = 0.7, 0.3

        weights_by_code[code] = (wm, wh)

    return weights_by_code
