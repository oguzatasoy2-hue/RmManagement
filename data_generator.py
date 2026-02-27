import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ==========================================
# GÉNÉRATEUR DE DONNÉES YIELD MANAGEMENT
# ==========================================

# Configuration du générateur
START_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
DAYS_TO_SIMULATE = 90  # Prochains 3 mois
OUR_HOTEL_NAME = "Contact Hotel Le Provençal Bordeaux Lac"
TOTAL_ROOMS = 50 # Capacité de notre hôtel

COMPSET = {
    # Nom : [Positionnement Prix, Note Qualité sur 10]
    "Campanile Bordeaux - Le Lac": [1.05, 7.8],
    "Premiere Classe Bordeaux Nord": [0.85, 6.5],
    "All Suites Appart Hotel Bordeaux Lac": [1.15, 8.2],
    "Mercure Bordeaux Lac": [1.40, 8.6]
}

# Prix de base (Ajusté pour un 3 étoiles à Bordeaux Lac)
BASE_PRICE = 85

# Événements spéciaux
SPECIAL_EVENTS = {
    15: {"name": "Congrès Vinexpo", "mult": 1.8},
    16: {"name": "Congrès Vinexpo", "mult": 1.8},
    45: {"name": "Festival de l'Atlantique", "mult": 1.5},
    46: {"name": "Festival de l'Atlantique", "mult": 1.5},
    75: {"name": "Match Bordeaux-Paris", "mult": 2.0}
}

def generate_market_data():
    """Génère un jeu de données de Yield Management avancé."""
    
    records = []
    
    for day in range(DAYS_TO_SIMULATE):
        current_date = START_DATE + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 1. Calcul de la Demande Marché
        is_weekend = current_date.weekday() in [4, 5]
        weekend_multiplier = 1.3 if is_weekend else 1.0
        
        event_info = SPECIAL_EVENTS.get(day, {"name": "Non", "mult": 1.0})
        event_multiplier = event_info["mult"]
        
        seasonality = 1.0 + (day / DAYS_TO_SIMULATE) * 0.2
        market_multiplier = weekend_multiplier * event_multiplier * seasonality
        
        # 2. Génération CompSet
        compset_prices = []
        for comp_name, stats in COMPSET.items():
            pos_price_factor = stats[0]
            review_score = stats[1]
            
            daily_noise = random.uniform(0.95, 1.05)
            final_price = BASE_PRICE * market_multiplier * pos_price_factor * daily_noise
            final_price = round(final_price, 2)
            compset_prices.append(final_price)
            
            # Occupation des concurrents (souvent plus élevée si l'évènement est fort)
            market_occ = min(0.98, random.uniform(0.6, 0.90) * (market_multiplier/1.2))
            
            records.append({
                "Date": date_str,
                "Hotel": comp_name,
                "Is_Compset": True,
                "Price": final_price,
                "Occupancy_Rate": round(market_occ, 2),
                "Rooms_Sold": int(TOTAL_ROOMS * market_occ), # Simulation
                "Review_Score": review_score,
                "Event": event_info["name"]
            })
            
        # 3. Génération de NOTRE HÔTEL (Le Provençal)
        market_average = round(sum(compset_prices) / len(compset_prices), 2)
        
        # Scénario Yield: On est parfois mal positionné pour montrer l'utilité du dashboard
        if event_multiplier > 1.0:
            our_price = market_average * 0.85 # Mince, on est trop peu cher pendant l'event !
            our_occ = 0.98 # On est complet trop tôt
            rooms_sold_ly = int(TOTAL_ROOMS * 0.85) # L'an dernier on n'était pas plein
        elif is_weekend:
            our_price = market_average * random.uniform(0.98, 1.02)
            our_occ = 0.85
            rooms_sold_ly = int(TOTAL_ROOMS * 0.80)
        else:
            our_price = market_average * 1.15 # Trop cher en semaine
            our_occ = 0.55
            rooms_sold_ly = int(TOTAL_ROOMS * 0.65)
            
        our_price = round(our_price, 2)
        rooms_sold = int(TOTAL_ROOMS * our_occ)
        
        # --- NOUVELLES METRIQUES DE YIELD ---
        # Pace (Rythme de réservation) : est-ce qu'on est en avance ou en retard sur N-1 ?
        # Pickup (Ramassage) : Combien de chambres vendues sur les 7 derniers jours
        pickup_7d = int(random.uniform(0, rooms_sold * 0.3)) if day > 7 else random.randint(1, 5)
        
        # No-Show probabilité (pour l'Overbooking)
        no_show_rate = round(random.uniform(0.01, 0.08), 2)
        
        records.append({
            "Date": date_str,
            "Hotel": OUR_HOTEL_NAME,
            "Is_Compset": False,
            "Price": our_price,
            "Occupancy_Rate": round(our_occ, 2),
            "Rooms_Sold": rooms_sold,
            "Rooms_Sold_LY": rooms_sold_ly, # Ventes à la même date l'An Dernier
            "Pickup_7d": pickup_7d,
            "Capacity": TOTAL_ROOMS,
            "No_Show_Rate": no_show_rate,
            "Review_Score": 7.5, # Notre note
            "RevPAR": round(our_price * our_occ, 2),
            "Market_Avg_Price": market_average,
            "ARI": round((our_price / market_average) * 100, 2), # Rate Index
            "Event": event_info["name"]
        })

    # Sauvegarde
    df = pd.DataFrame(records)
    os.makedirs('data', exist_ok=True)
    filepath = 'data/hotel_market_data.csv'
    df.to_csv(filepath, index=False)
    
    print(f"✅ Fichier Yield Management généré : {filepath}")
    return df

if __name__ == "__main__":
    generate_market_data()
