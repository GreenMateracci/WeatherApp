import streamlit as st
from weather_api import get_cities
import plotly.express as plt
import pandas as pd

st.set_page_config(
    layout="wide",
    page_title="City Weather Explorer",
    page_icon = "🌤"
)

st.title("City Weather Explorer")
st.markdown("Compare weather data across multiple cities (Open sidebar)")

st.sidebar.header("Search Parameters")

cities_input = st.sidebar.text_input(
    "Enter cities (comma separated)"
)

aggregation = st.sidebar.selectbox(
    "Aggregation Level",
    ["Daily", "Weekly", "Monthly"]
)

start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

fetch_button = st.sidebar.button("Fetch Data")
if fetch_button:
    cities = [city.strip() for city in cities_input.split(",")]

    with st.spinner("Fetching weather data..."):
        try:
            cities_data = get_cities(cities,start_date,end_date)
            st.success("Data fetched successfully")
            #st.dataframe(cities_data)
            if aggregation == "Daily":
                aggregated_data = cities_data.copy()
            elif aggregation == "Weekly":
                aggregated_data = (cities_data.groupby(["city",pd.Grouper(key="date", freq="W")]).mean(numeric_only=True).reset_index())
            elif aggregation == "Monthly":
                aggregated_data = cities_data.groupby(["city",pd.Grouper(key="date",freq="ME")]).mean().reset_index()

            cities_data_by_city = cities_data.groupby("city").agg({
                "daily_temperature_max": "mean",
                "daily_temperature_min": "mean",
                "daily_precipitation": "sum",
                "daily_wind_speed": "mean",
            }).round(2)
            cities_data_by_city.columns = ["Avg Max Temp (°C)", "Avg Min Temp (°C)", "Avg Precipitation (mm)", "Avg Wind Speed (km/h)"]
            st.subheader("City statistics")
            st.dataframe(cities_data_by_city)

            aggregated_data["average_daily_temperature"] = (aggregated_data["daily_temperature_max"] + aggregated_data["daily_temperature_min"])/2

            st.subheader("Temperatures")
            temp_chart_data = plt.line(
                aggregated_data,
                x = "date",
                y = "average_daily_temperature",
                color = "city",
                title = "Average Temperatures Over Time (°C)",
                labels = {"average_daily_temperature": "average daily temperature"}
            )
            st.plotly_chart(temp_chart_data)

            aggregated_data["temperature_amplitude"] = (
                    aggregated_data["daily_temperature_max"] - aggregated_data["daily_temperature_min"]
            ).abs()

            st.subheader("Temperature Amplitude")
            temp_chart_data = plt.line(
                aggregated_data,
                x="date",
                y="temperature_amplitude",
                color="city",
                title="Temperature Amplitude Over Time (°C)",
                labels = {"temperature_amplitude": "temperature amplitude"}
            )
            st.plotly_chart(temp_chart_data)

            st.subheader("Precipitation")
            temp_chart_data = plt.line(
                aggregated_data,
                x = "date",
                y = "daily_precipitation",
                color = "city",
                title = "Precipitation Over Time (mm)",
                labels = {"daily_precipitation": "daily precipitation"}
            )
            st.plotly_chart(temp_chart_data, use_container_width=True)



        except Exception as e:
            st.error(f"Error: {e}")