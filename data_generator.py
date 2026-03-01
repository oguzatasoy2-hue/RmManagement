import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ==========================================
# GÉNÉRATEUR DE DONNÉES RM AVANCÉ (PRO SAAS)
# ==========================================

OUR_HOTEL_NAME = "Contact Hotel Le Provençal Bordeaux Lac"
TOTAL_ROOMS = 50 
BASE_PRICE = 85

COMPSET = {
    "Campanile Bordeaux - Le Lac": [1.05, 7.8],
    "Premiere Classe Bordeaux Nord": [0.85, 6.5],
    "All Suites Appart Hotel Bordeaux Lac": [1.15, 8.2],
    "Mercure Bordeaux Lac": [1.40, 8.6]
}

COMPSET_TEMPLATES = {
    1: {"Formule 1 Économique": [0.90, 5.5], "Ibis Budget Centre": [1.05, 6.2], "Première Classe": [0.95, 5.8]},
    2: {"Campanile Centre": [1.05, 6.8], "Ibis Budget": [0.95, 6.5], "B&B Hotel": [1.00, 7.0]},
    3: {"Campanile Confort": [1.05, 7.8], "All Suites Appart": [1.15, 8.2], "Mercure Centre": [1.40, 8.6]},
    4: {"Mercure Prestige": [0.90, 8.5], "Novotel Centre": [1.05, 8.8], "Best Western Plus": [1.10, 8.7]},
    5: {"Sofitel Luxe": [1.10, 9.2], "InterContinental": [1.20, 9.5], "Grand Hyatt": [1.30, 9.4]}
}

CITY_EVENTS = {
    "Bordeaux": {15: {"name": "Congrès Vinexpo", "mult": 1.8}, 45: {"name": "Festival Atlantique", "mult": 1.5}, 75: {"name": "Match FCBG-PSG", "mult": 2.0}, 110: {"name": "Fête du Vin", "mult": 2.2}, 180: {"name": "Marathon de Bordeaux", "mult": 1.7}, 240: {"name": "Rentrée Étudiante", "mult": 1.4}, 320: {"name": "Marché de Noël", "mult": 1.6}},
    "Paris": {10: {"name": "Salon Agriculture", "mult": 1.6}, 30: {"name": "Fashion Week", "mult": 2.0}, 60: {"name": "Roland-Garros", "mult": 1.8}, 150: {"name": "14 Juillet", "mult": 2.5}, 200: {"name": "Jeux Olympiques (Annif)", "mult": 2.3}, 280: {"name": "Mondial de l'Auto", "mult": 1.9}, 350: {"name": "Nouvel An", "mult": 2.8}},
    "Lyon": {20: {"name": "Fête des Lumières", "mult": 2.5}, 50: {"name": "Salon Sirha", "mult": 1.9}, 120: {"name": "Nuits Sonores", "mult": 1.6}, 210: {"name": "Foire de Lyon", "mult": 1.5}, 300: {"name": "Run in Lyon", "mult": 1.4}},
    "Nice": {12: {"name": "Carnaval", "mult": 1.9}, 40: {"name": "Festival de Cannes", "mult": 2.5}, 90: {"name": "Grand Prix Monaco", "mult": 3.0}, 180: {"name": "Nice Jazz Festival", "mult": 1.8}, 250: {"name": "Ironman", "mult": 2.1}},
    "Marseille": {18: {"name": "Congrès Médical", "mult": 1.4}, 42: {"name": "OM Match", "mult": 1.8}, 110: {"name": "Foire de Marseille", "mult": 1.5}, 160: {"name": "Delta Festival", "mult": 1.9}, 240: {"name": "Défi Monte-Cristo", "mult": 1.6}},
    "Autre": {20: {"name": "Salon Pro", "mult": 1.6}, 50: {"name": "Festival", "mult": 1.5}, 100: {"name": "Événement Régional", "mult": 1.3}, 200: {"name": "Saison Haute", "mult": 1.7}, 300: {"name": "Fête Locale", "mult": 1.4}}
}

def generate_market_data():
    """Version par défaut pour le chargement initial."""
    return generate_custom_data(OUR_HOTEL_NAME, 3, TOTAL_ROOMS, BASE_PRICE, "Bordeaux", is_default=True)

def generate_custom_data(hotel_name, stars, total_rooms, base_price, city, is_default=False):
    """Génère un jeu de données simulant un véritable environnement SaaS (Passé + Futur, Parité, Recherches)."""
    
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    compset = COMPSET if is_default else COMPSET_TEMPLATES.get(stars, COMPSET_TEMPLATES[3])
    events = CITY_EVENTS.get(city, CITY_EVENTS["Autre"])
    review_score_base = min(10.0, 5.5 + stars * 0.8 + random.uniform(-0.3, 0.3))
    
    records = []
    
    # Simulation de -30 jours (STR Benchmark historique) à +365 jours (Forecasting Global)
    for day_offset in range(-30, 365):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        
        is_weekend = current_date.weekday() in [4, 5]
        weekend_multiplier = 1.3 if is_weekend else 1.0
        
        event_info = events.get(day_offset, {"name": "Non", "mult": 1.0})
        event_multiplier = event_info["mult"]
        
        seasonality = 1.0 + ((day_offset + 30) / 120) * 0.2
        market_multiplier = weekend_multiplier * event_multiplier * seasonality
        
        # --- MARKET INSIGHTS (Données prédictives) ---
        # Search Volume Index (0-100)
        base_search = 30 + (seasonality * 10)
        search_volume = int(min(100, base_search * event_multiplier * random.uniform(0.9, 1.2)))
        
        # --- COMPSET GENERATION ---
        compset_prices = []
        for comp_name, stats in compset.items():
            pos_price_factor = stats[0]
            comp_review = stats[1]
            
            daily_noise = random.uniform(0.95, 1.05)
            comp_price = round(base_price * market_multiplier * pos_price_factor * daily_noise, 2)
            compset_prices.append(comp_price)
            
            comp_occ = min(0.98, random.uniform(0.6, 0.90) * (market_multiplier / 1.2))
            
            records.append({
                "Date": date_str,
                "Hotel": comp_name,
                "Is_Compset": True,
                "Price": comp_price,
                "OTA_Price": comp_price, # On assume que les concurrents ont la parité
                "Occupancy_Rate": round(comp_occ, 2),
                "Rooms_Sold": int(total_rooms * comp_occ),
                "Review_Score": comp_review,
                "Event": event_info["name"],
                "Search_Volume": search_volume
            })
            
        # --- OUR HOTEL GENERATION ---
        market_average = round(sum(compset_prices) / len(compset_prices), 2)
        
        if event_multiplier > 1.0:
            our_price = market_average * 0.85 # Mince, on est trop peu cher pendant l'event (Mauvais RM)
            our_occ = 0.98
            rooms_sold_ly = int(total_rooms * 0.85)
        elif is_weekend:
            our_price = market_average * random.uniform(0.98, 1.02)
            our_occ = 0.85
            rooms_sold_ly = int(total_rooms * 0.80)
        else:
            our_price = market_average * 1.15 # Trop cher en semaine
            our_occ = 0.55
            rooms_sold_ly = int(total_rooms * 0.65)
            
        our_price = round(our_price, 2)
        rooms_sold = int(total_rooms * our_occ)
        
        # --- PARITY INSIGHT ---
        # 15% du temps, Booking/Expedia nous vend moins cher (Perte de marge)
        has_parity_issue = random.random() < 0.15
        ota_margin_cut = random.uniform(0.85, 0.92) if has_parity_issue else 1.0
        our_ota_price = round(our_price * ota_margin_cut, 2)
        
        # --- YIELD METRICS ---
        pickup_7d = int(random.uniform(0, rooms_sold * 0.3)) if day_offset > -23 else random.randint(1, 5)
        no_show_rate = round(random.uniform(0.01, 0.08), 2)
        sentiment_daily = round(review_score_base + random.uniform(-0.2, 0.2), 1)
        
        # --- ADVANCED AI FORECASTING VARIABLES ---
        # 1. Pace Velocity: Vitesse de remplissage comparée à N-1
        pace_velocity_pct = round(random.uniform(-10.0, 15.0), 1) # ex: +15% d'avance sur l'an dernier
        if event_multiplier > 1.0:
            pace_velocity_pct += 12.0 # Forte vélocité lors des événements
            
        # 2. Price Elasticity: Sensibilité au prix (Plus on approche de 0, moins le client est sensible au prix)
        # En semaine corporate: forte inélasticité. En week-end loisir: plus forte élasticité.
        base_elasticity = -1.5 if is_weekend else -0.8
        price_elasticity = round(base_elasticity * (2.0 - event_multiplier), 2)
        
        # 3. Willingness To Pay (WTP) - Modèle Probabiliste
        # Prix psychologique maximal que le marché est prêt à payer pour ce jour précis
        wtp_max = round(market_average * 1.35 * event_multiplier * (1 + (sentiment_daily - 7)/10), 0)

        records.append({
            "Date": date_str,
            "Hotel": hotel_name,
            "Is_Compset": False,
            "Price": our_price,
            "OTA_Price": our_ota_price, # Prix diffusé sur Booking
            "Occupancy_Rate": round(our_occ, 2),
            "Rooms_Sold": rooms_sold,
            "Rooms_Sold_LY": rooms_sold_ly,
            "Pickup_7d": pickup_7d,
            "Capacity": total_rooms,
            "No_Show_Rate": no_show_rate,
            "Review_Score": sentiment_daily,
            "RevPAR": round(our_price * our_occ, 2),
            "Market_Avg_Price": market_average,
            "ARI": round((our_price / market_average) * 100, 2),
            "Event": event_info["name"],
            "Search_Volume": search_volume,
            "Pace_Velocity_Pct": pace_velocity_pct,
            "Price_Elasticity": price_elasticity,
            "Willingness_To_Pay": wtp_max
        })
        
    df = pd.DataFrame(records)
    
    if is_default:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
        filepath = os.path.join(os.path.dirname(__file__), 'data', 'hotel_market_data.csv')
        df.to_csv(filepath, index=False)
        print(f"✅ Fichier Pro SaaS généré : {filepath}")
        
    return df

if __name__ == "__main__":
    generate_market_data()
