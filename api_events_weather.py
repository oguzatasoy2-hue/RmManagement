import requests
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

@st.cache_data(ttl=3600, show_spinner="Connexion PredictHQ (Événements Réels)...")
def get_real_events(city, start_date, end_date):
    """
    Fetches real events from PredictHQ for a given city and date range.
    """
    API_TOKEN = 'Mt4VSz_0wRYddGpel9HnV-YRcOyU9ASsfP4BLOMi'
    
    # Mapping cities to rough lat/lon for PredictHQ
    city_coords = {
        "Paris": "48.8566,2.3522",
        "Marseille": "43.2965,5.3698",
        "Lyon": "45.7640,4.8357",
        "Bordeaux": "44.8378,-0.5792",
        "Nice": "43.7102,7.2620"
    }
    
    location = city_coords.get(city, "48.8566,2.3522") # Default Paris
    
    url = "https://api.predicthq.com/v1/events/"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "within": f"20km@{location}", # Strict geographic boundary
        "start.gte": start_date,
        "start.lte": end_date,
        "sort": "rank", # Get most impactful events first within this area
        "limit": 10
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for result in data.get('results', []):
            events.append({
                "title": result.get("title"),
                "date": result.get("start")[0:10], # Extract YYYY-MM-DD
                "rank": result.get("rank"), # Impact score 0-100
                "category": result.get("category")
            })
        return events
    except Exception as e:
        print(f"PredictHQ Error: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner="Connexion OpenWeatherMap (Météo Réelle)...")
def get_real_weather(city):
    """
    Fetches 5-day weather forecast from OpenWeatherMap.
    """
    API_KEY = 'eae4263a93e7719beb819184b1227a2e'
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=fr"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        forecast = {}
        # The API returns data every 3 hours. We'll pick one reading per day (e.g. at 12:00)
        for item in data.get('list', []):
            dt_txt = item['dt_txt']
            if "12:00:00" in dt_txt: # Grab the midday forecast
                date = dt_txt.split(" ")[0]
                forecast[date] = {
                    "temp": item['main']['temp'],
                    "description": item['weather'][0]['description'].capitalize(),
                    "icon": item['weather'][0]['icon']
                }
        return forecast
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"OpenWeatherMap Error: API Key {API_KEY} is either invalid or not yet activated (can take 1-2 hours for new keys).")
        else:
            print(f"OpenWeatherMap HTTP Error: {e}")
        return {}
    except Exception as e:
        print(f"OpenWeatherMap Error: {e}")
        return {}

def test_apis():
    print("Testing APIs...")
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    print("\n--- Testing PredictHQ (Paris) ---")
    events = get_real_events("Paris", today, next_week)
    for e in events:
        print(e)
        
    print("\n--- Testing OpenWeatherMap (Paris) ---")
    weather = get_real_weather("Paris")
    print(weather)

if __name__ == "__main__":
    test_apis()
