import pandas as pd
import requests_cache as rqc
import openmeteo_requests
from retry_requests import retry

cached_session = rqc.CachedSession(cache_name="weather_cache", expire_after=86400)
retry_session = retry(cached_session)
meteo = openmeteo_requests.Client(session=retry_session)

def get_weather_data(city_name, start_date, end_date):
    city = get_city_coords(city_name)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_min","temperature_2m_max","precipitation_sum","snowfall_sum","wind_speed_10m_max"],
    }
    responses = meteo.weather_api(url,params)
    return responses

def get_city_coords(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search/?name={city_name}&count=1&language=en"
    response = cached_session.get(url)
    result = response.json().get('results')
    data = {
        'city': city_name,
        'latitude': result[0]['latitude'],
        'longitude': result[0]['longitude'],
    }
    return data

def get_cities(cities_list, start_date, end_date):
    all_cities = []
    for city in cities_list:
        city_data = get_weather_data(city, start_date, end_date)
        city_data_processed = process_city_data(city_data,city)
        all_cities.append(city_data_processed)

    return pd.concat(all_cities, ignore_index=True)

def process_city_data(city_data,city_name):
    response = city_data[0]
    daily = response.Daily()
    daily_temperature_min = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_max = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation = daily.Variables(2).ValuesAsNumpy()
    daily_snowfall = daily.Variables(3).ValuesAsNumpy()
    daily_wind_speed = daily.Variables(4).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ), "daily_temperature_min": daily_temperature_min,
        "daily_temperature_max": daily_temperature_max,
        "daily_precipitation": daily_precipitation,
        "daily_snowfall": daily_snowfall,
        "daily_wind_speed": daily_wind_speed}

    daily_dataframe = pd.DataFrame(daily_data)

    daily_dataframe["city"] = city_name
    return daily_dataframe

df = get_cities(["Frankfurt","Kuala Lumpur"],"2026-01-01","2026-04-01")
df.to_csv("weather_data.csv")


