import pandas as pd
from datetime import datetime
from amadeus import Client, ResponseError
import streamlit as st

# Setup Amadeus Client (Using Streamlit caching to prevent spamming the free API)
@st.cache_data(ttl=3600, show_spinner="Connexion au GDS Amadeus (Live Data)...")
def get_flight_market_demand(origin_code, dest_code, departure_date):
    """
    Fetches real-time flight offers from Amadeus Sandbox to gauge market compression.
    Returns a dictionary with average price, minimum price, and total offers found.
    """
    # Replace with environment variables in a real production app
    API_KEY = '8XIBoI5A3GV6bzlKBb4lPDuqRSjmDtOH'
    API_SECRET = 'ESSWhHJ1rgY97GFY'
    
    amadeus = Client(
        client_id=API_KEY,
        client_secret=API_SECRET
    )

    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_code,
            destinationLocationCode=dest_code,
            departureDate=departure_date,
            adults=1,
            max=50 # Grab up to 50 flights to get a good average
        )
        
        offers = response.data
        if not offers:
            return {"status": "success", "offers_count": 0, "avg_price": 0.0, "min_price": 0.0}

        prices = [float(offer['price']['total']) for offer in offers]
        
        return {
            "status": "success",
            "offers_count": len(prices),
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": round(min(prices), 2),
            "currency": offers[0]['price']['currency'] if offers else "EUR"
        }

    except ResponseError as error:
        print(f"Amadeus API Error: {error}")
        return {"status": "error", "message": str(error)}
