# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 10:51:12 2026

@author: marco
"""

import os


def get_project_root():
    try:
        # Works when running as a script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(script_dir)  # parent of modeling/, geocoding/, etc.
    except NameError:
        # Works in Jupyter or interactive mode
        return os.getcwd()


PROJECT_ROOT = get_project_root()
print("Project root:", PROJECT_ROOT)


def get_dataset_path(filename):
    return os.path.join(PROJECT_ROOT, "dataset", filename)


def get_model_path(filename):
    return os.path.join(PROJECT_ROOT, "models", filename)


def get_plot_path(filename):
    return os.path.join(PROJECT_ROOT, "plots", filename)


def get_report_path(filename):
    return os.path.join(PROJECT_ROOT, "report", filename)
