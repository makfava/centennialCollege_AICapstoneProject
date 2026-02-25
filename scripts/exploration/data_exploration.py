# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 14:09:57 2026

@author: marco
"""

import pandas as pd
import matplotlib.pyplot as plt
import folium
import seaborn as sns
from scipy.stats import chi2_contingency
from folium.plugins import HeatMap
from scripts.paths import get_plot_path, get_report_path


# -----------------------------
# Geospatial visualization
# -----------------------------


# Heatmap
def plot_vehicle_heatmaps(df):
    # Initialize map centered on Toronto
    m = folium.Map(location=[43.7, -79.4], zoom_start=11)

    # Vehicle type colors (not directly used in HeatMap, but useful if you want markers too)
    vehicle_types = ["BUS", "STREETCAR", "SUBWAY"]

    for vehicle_type in vehicle_types:
        subset = df[(df["Vehicle_Type"] == vehicle_type) & df["Latitude"].notna() & df["Longitude"].notna()]
        heat_data = subset[["Latitude", "Longitude"]].values.tolist()

        # Create a feature group for each vehicle type
        fg = folium.FeatureGroup(name=vehicle_type)

        HeatMap(heat_data, radius=8, blur=6, max_zoom=13).add_to(fg)

        # Add feature group to map
        m.add_child(fg)

    # Add layer control (checkboxes)
    folium.LayerControl(collapsed=False).add_to(m)

    return m


# TOP 20 Incident location per transportation type
def plot_top_locations(df, vehicle_type):
    subset = df[df["Vehicle_Type"] == vehicle_type]
    top_locations = subset["Station"].value_counts().head(20)

    plt.figure(figsize=(10, 6))
    ax = top_locations.plot(kind="bar", color="steelblue")
    plt.title(f"Top 20 Incident Locations ({vehicle_type})")
    plt.ylabel("Number of Incidents")

    # Rotate tick labels 45 degrees for readability
    plt.xticks(rotation=45, ha="right")

    # Add numbers on top of each bar, centered horizontally
    for p in ax.patches:
        ax.annotate(
            str(int(p.get_height())),
            (p.get_x() + p.get_width() / 2.0, p.get_height() + 50),  # spacing above bar
            ha="center",
            va="bottom",
            fontsize=9,
            color="black",
            rotation=45,
        )

    # Expand y-axis limit so labels don’t overlap the border
    ax.set_ylim(0, max(top_locations) * 1.10)

    # Remove top and right spines (borders)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    # Save plot to plots folder
    filename = f"top_locations_{vehicle_type.lower()}.png"
    plt.savefig(get_plot_path(filename))
    print(f"Saved plot: {filename}")

    # plt.show()

    print(f"\nTop 20 {vehicle_type} incident locations:\n")
    print(top_locations)


# TOP 20 Incident cause per transportation type
def plot_top_causes(df, vehicle_type):
    subset = df[df["Vehicle_Type"] == vehicle_type]

    # Count top 20 causes using the enriched 'Cause' column
    top_causes = subset["Description"].value_counts().head(20)

    plt.figure(figsize=(10, 6))
    ax = top_causes.plot(kind="bar", color="darkorange")
    plt.title(f"Top 20 Causes of Incidents ({vehicle_type})")
    plt.ylabel("Number of Incidents")

    # Rotate tick labels
    plt.xticks(rotation=45, ha="right")

    # Add numbers on top of each bar
    for p in ax.patches:
        ax.annotate(
            str(int(p.get_height())),
            (p.get_x() + p.get_width() / 2.0, p.get_height() + 50),
            ha="center",
            va="bottom",
            fontsize=9,
            color="black",
            rotation=45,
        )

    # Expand y-axis
    ax.set_ylim(0, top_causes.max() * 1.10)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    # Save plot to plots folder
    filename = f"top_causes_{vehicle_type.lower()}.png"
    plt.savefig(get_plot_path(filename))
    print(f"Saved plot: {filename}")

    # plt.show()

    # Print top 20 causes with counts
    print(f"\nTop 20 {vehicle_type} incident causes:")
    print(top_causes)


# -----------------------------
# Function for correlation analysis
# -----------------------------
def correlation_analysis(df, vehicle_type, top_n_causes=12, top_n_stations=20, save=True):
    subset = df[df["Vehicle_Type"] == vehicle_type].copy()
    print(f"\n=== Correlation Analysis for {vehicle_type} ===")

    # --- Restrict to most frequent causes ---
    top_causes = subset["Description"].value_counts().head(top_n_causes).index
    subset = subset[subset["Description"].isin(top_causes)]

    # --- Day vs Cause heatmap ---
    pivot_day_cause = (
        subset.pivot_table(index="DayOfWeek", columns="Description", values="Station", aggfunc="count")
        .fillna(0)
        .astype(int)
    )

    plt.figure(figsize=(14, 6))
    ax = sns.heatmap(pivot_day_cause, cmap="Blues", annot=True, fmt="d")
    plt.title(f"Incidents by Day and Cause ({vehicle_type})")
    plt.xlabel("Cause of Accident")
    plt.ylabel("Day of Week")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    if save:
        plt.savefig(get_plot_path(f"{vehicle_type.lower()}_day_vs_cause.png"))
    # plt.show()

    # --- Hour vs Cause heatmap ---
    pivot_hour_cause = (
        subset.pivot_table(index="Description", columns="Hour", values="Station", aggfunc="count").fillna(0).astype(int)
    )

    plt.figure(figsize=(14, 8))
    ax = sns.heatmap(pivot_hour_cause, cmap="Reds", annot=True, fmt="d")
    plt.title(f"Incidents by Hour and Cause ({vehicle_type})")
    plt.xlabel("Hour of Day")
    plt.ylabel("Cause of Accident")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    plt.tight_layout()
    if save:
        plt.savefig(get_plot_path(f"{vehicle_type.lower()}_hour_vs_cause.png"))
    # plt.show()

    # --- Top stations vs Cause heatmap ---
    top_stations = subset["Station"].value_counts().head(top_n_stations).index
    pivot_station_cause = (
        subset[subset["Station"].isin(top_stations)]
        .pivot_table(index="Station", columns="Description", values="Hour", aggfunc="count")
        .fillna(0)
        .astype(int)
    )

    plt.figure(figsize=(14, 10))
    ax = sns.heatmap(pivot_station_cause, cmap="Greens", annot=True, fmt="d")
    plt.title(f"Top {top_n_stations} Stations by Cause ({vehicle_type})")
    plt.xlabel("Cause of Accident")
    plt.ylabel("Station")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    plt.tight_layout()
    if save:
        plt.savefig(get_plot_path(f"{vehicle_type.lower()}_station_vs_cause.png"))
    # plt.show()

    # --- Chi-square tests ---
    contingency_day = pd.crosstab(subset["DayOfWeek"], subset["Description"])
    chi2, p, dof, expected = chi2_contingency(contingency_day)
    print(f"Chi-square test (Cause vs Day) for {vehicle_type}: chi2={chi2:.2f}, p-value={p:.4f}")

    contingency_hour = pd.crosstab(subset["Hour"], subset["Description"])
    chi2, p, dof, expected = chi2_contingency(contingency_hour)
    print(f"Chi-square test (Cause vs Hour) for {vehicle_type}: chi2={chi2:.2f}, p-value={p:.4f}")

    contingency_station = pd.crosstab(subset["Station"], subset["Description"])
    chi2, p, dof, expected = chi2_contingency(contingency_station)
    print(f"Chi-square test (Cause vs Station) for {vehicle_type}: chi2={chi2:.2f}, p-value={p:.4f}")

    # --- Summary report: counts + percentages ---
    print(f"\n--- Incident Report for {vehicle_type} ---")
    cause_counts = subset["Description"].value_counts()
    total_incidents = cause_counts.sum()

    report_df = pd.DataFrame({"Count": cause_counts, "Percentage": (cause_counts / total_incidents * 100).round(2)})

    print(report_df)
    print(f"\nTotal incidents analyzed: {total_incidents}")

    if save:
        report_df.to_csv(get_report_path(f"{vehicle_type.lower()}_incident_report.csv"))
        print(f"Report saved: {vehicle_type.lower()}_incident_report.csv")


# Follium map for the top 20 station for number of incident with description
def plot_combined_map(df):
    # Initialize map centered on Toronto
    m = folium.Map(location=[43.7, -79.4], zoom_start=11)

    # Vehicle type colors
    colors = {"BUS": "red", "STREETCAR": "blue", "SUBWAY": "green"}

    for vehicle_type in ["BUS", "STREETCAR", "SUBWAY"]:
        subset = df[df["Vehicle_Type"] == vehicle_type]

        # Count incidents per station
        station_counts = subset["Station"].value_counts().reset_index()
        station_counts.columns = ["Station", "Total"]

        # Keep top 20 stations
        top20_stations = station_counts.head(20)["Station"]

        # Aggregate causes per station
        station_cause_counts = subset.groupby(["Station", "Description"]).size().reset_index(name="Count")

        # Coordinates per station
        station_coords = subset.groupby("Station")[["Latitude", "Longitude"]].mean().reset_index()

        # Merge totals and coords
        station_summary = station_counts.merge(station_coords, on="Station", how="left")
        station_summary = station_summary[station_summary["Station"].isin(top20_stations)]

        # Create a feature group for each vehicle type
        fg = folium.FeatureGroup(name=vehicle_type)

        for _, row in station_summary.iterrows():
            station = row["Station"]
            total = row["Total"]
            lat, lon = row["Latitude"], row["Longitude"]

            # Get cause breakdown for this station (alphabetical order)
            causes = station_cause_counts[station_cause_counts["Station"] == station].sort_values("Description")

            # Build popup text with scrollbar
            popup_html = f"""
            <div style="max-height:200px; overflow-y:auto;">
            <b>Station:</b> {station}<br>
            <b>Total Incidents:</b> {total}<br><br>
            <b>Causes:</b><br>
            """
            for _, c in causes.iterrows():
                popup_html += f"- {c['Description']}: {c['Count']}<br>"
            popup_html += "</div>"

            # Custom pin with number
            color = colors[vehicle_type]
            fg.add_child(
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=station,  # hover shows station/street name
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="transform: translate(-50%, -50%);">
                            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="40">
                                <path d="M15 0 C23 0 30 7 30 15 C30 25 15 40 15 40 C15 40 0 25 0 15 C0 7 7 0 15 0 Z"
                                      fill="{color}" stroke="black" stroke-width="1"/>
                                <text x="15" y="22" text-anchor="middle" font-size="12" font-weight="bold" fill="white">{total}</text>
                            </svg>
                        </div>
                        """
                    ),
                )
            )

        # Add feature group to map
        m.add_child(fg)

    # Add layer control (checkboxes)
    folium.LayerControl(collapsed=False).add_to(m)

    # Add custom legend with colored circles
    legend_html = """
     <div style="
     position: fixed; 
     bottom: 50px; left: 50px; width: 180px; height: 120px; 
     background-color: white; 
     border:2px solid grey; z-index:9999; font-size:14px;
     padding: 10px; opacity: 0.9;">
     <b>Legend</b><br>
     <div style="display:flex; align-items:center;">
         <div style="width:15px; height:15px; background-color:red; border-radius:50%; margin-right:8px;"></div>
         Bus
     </div>
     <div style="display:flex; align-items:center;">
         <div style="width:15px; height:15px; background-color:blue; border-radius:50%; margin-right:8px;"></div>
         Streetcar
     </div>
     <div style="display:flex; align-items:center;">
         <div style="width:15px; height:15px; background-color:green; border-radius:50%; margin-right:8px;"></div>
         Subway
     </div>
     </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def run_exploration(df):
    print("=== Running Exploration ===")

    if "Datetime" not in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.time
        df["Datetime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str))
    # Ensure derived time features exist
    if "DayOfWeek" not in df.columns:
        df["DayOfWeek"] = df["Datetime"].dt.day_name()
    if "Hour" not in df.columns:
        df["Hour"] = df["Datetime"].dt.hour

    # Combined heatmap
    combined_heatmap = plot_vehicle_heatmaps(df)
    combined_heatmap.save(get_plot_path("incidents_heatmap.html"))

    # Top locations per vehicle type
    plot_top_locations(df, "BUS")
    plot_top_locations(df, "STREETCAR")
    plot_top_locations(df, "SUBWAY")

    # Generate plots per transportation type
    plot_top_causes(df, "BUS")
    plot_top_causes(df, "STREETCAR")
    plot_top_causes(df, "SUBWAY")

    # Correlation analysis per vehicle type
    correlation_analysis(df, "BUS")
    correlation_analysis(df, "STREETCAR")
    correlation_analysis(df, "SUBWAY")

    # Run correlation analysis for each vehicle type
    correlation_analysis(df, "BUS", top_n_causes=12, top_n_stations=20)
    correlation_analysis(df, "STREETCAR", top_n_causes=12, top_n_stations=20)
    correlation_analysis(df, "SUBWAY", top_n_causes=12, top_n_stations=20)

    # Run 20 top station map with description
    combined_map = plot_combined_map(df)
    combined_map.save(get_plot_path("combined_incidents_map_with_legend.html"))

    print("Exploration complete")
