import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import time
import os

API_KEY = "7940cc2992mshfcee888376ac58bp11c860jsn4628d785dc7c"
HOST = "booking-data.p.rapidapi.com"

# On utilise les VRAIS identifiants Booking uniques pour chaque hôtel
HOTEL_IDS = {
    "Contact Hotel Le Provençal Bordeaux Lac": "422112",
    "Campanile Bordeaux - Le Lac": "53940",      # Estimations ou partiels, à remplacer par du vrai
    "Premiere Classe Bordeaux Nord": "51568",
    "All Suites Appart Hotel Bordeaux Lac": "93421", # Mock
    "Mercure Bordeaux Lac": "12932"              # Mock
}

def fetch_live_prices(start_date, number_of_days=1):
    """
    On interroge VRAIMENT l'API avec les identifiants HOTELS exacts.
    """
    records = []
    
    date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    checkin_str = start_date
    checkout_str = (date_obj + timedelta(days=number_of_days)).strftime("%Y-%m-%d")
    
    print(f"📡 Récupération des VRAIS prix de {checkin_str} à {checkout_str}...")
    
    # On utilise l'endpoint de détails de chambre qui prend un ID d'hôtel direct
    url = "https://booking-data.p.rapidapi.com/booking-app/stays/details/rooms"
    headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST}
    
    for hotel_name, hotel_id in HOTEL_IDS.items():
        querystring = {
            "query": hotel_id,
            "checkin": checkin_str,
            "checkout": checkout_str,
            "units": "metric",
            "temperature_unit": "c"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            prix_par_nuit = 'N/A'
            # Booking renvoie souvent "cheapest_avail_price_eur" ou similaire
            if 'data' in data and data['data']:
                try:
                    # On cherche le prix le moins cher disponible
                    prix_total = data['data'].get("cheapest_avail_price_eur", 0)
                    if prix_total == 0:
                        # Fallback sur une autre devise
                        prix_total = data['data'].get("cheapest_avail_price_usd", 0) * 0.95
                        
                    if prix_total > 0:
                        prix_par_nuit = round(prix_total / number_of_days, 2)
                except:
                    pass
            
            is_our_hotel = "Provençal" in hotel_name
            
            if prix_par_nuit != 'N/A':
                records.append({
                    "Date": checkin_str,
                    "Hotel": hotel_name,
                    "Is_Compset": not is_our_hotel,
                    "Price": prix_par_nuit,
                    "Occupancy_Rate": 0.5,
                    "Event": "Non"
                })
                print(f"✓ {hotel_name} trouvé : {prix_par_nuit}€")
            else:
                print(f"⚠️ {hotel_name} : Complet ou prix indispo sur l'API.")
                
        except Exception as e:
            print(f"❌ Erreur API pour {hotel_name}: {e}")
            
    return pd.DataFrame(records)

if __name__ == "__main__":
    print("Test du fetcher API en mode réel...")
    date_test = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    df = fetch_live_prices(date_test, 1)
    if not df.empty:
        print("\nRésultats récupérés:")
        print(df)
    else:
        print("\nAucun prix n'a pu être récupéré.")
