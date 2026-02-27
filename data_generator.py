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


# ==========================================
# GÉNÉRATEUR DE SIMULATION PERSONNALISÉE
# ==========================================

# Compétiteurs types par catégorie d'étoiles
COMPSET_TEMPLATES = {
    1: {
        "Formule 1 Économique": [0.90, 5.5],
        "Ibis Budget Centre": [1.05, 6.2],
        "Première Classe Gare": [0.95, 5.8],
        "HotelF1 Périphérie": [0.85, 5.0]
    },
    2: {
        "Campanile Centre": [1.05, 6.8],
        "Première Classe": [0.85, 6.0],
        "Ibis Budget": [0.95, 6.5],
        "B&B Hotel": [1.00, 7.0]
    },
    3: {
        "Campanile Confort": [1.05, 7.8],
        "Première Classe Premium": [0.85, 6.5],
        "All Suites Appart": [1.15, 8.2],
        "Mercure Centre": [1.40, 8.6]
    },
    4: {
        "Mercure Prestige": [0.90, 8.5],
        "Novotel Centre": [1.05, 8.8],
        "Best Western Plus": [1.10, 8.7],
        "Crowne Plaza": [1.25, 9.0]
    },
    5: {
        "Sofitel Luxe": [1.10, 9.2],
        "InterContinental": [1.20, 9.5],
        "Marriott Premium": [0.95, 9.0],
        "Grand Hyatt": [1.30, 9.4]
    }
}

# Événements par ville
CITY_EVENTS = {
    "Bordeaux": {
        15: {"name": "Congrès Vinexpo", "mult": 1.8},
        16: {"name": "Congrès Vinexpo", "mult": 1.8},
        45: {"name": "Festival de l'Atlantique", "mult": 1.5},
        46: {"name": "Festival de l'Atlantique", "mult": 1.5},
        75: {"name": "Match Bordeaux-Paris", "mult": 2.0}
    },
    "Paris": {
        10: {"name": "Salon de l'Agriculture", "mult": 1.6},
        11: {"name": "Salon de l'Agriculture", "mult": 1.6},
        30: {"name": "Fashion Week", "mult": 2.0},
        31: {"name": "Fashion Week", "mult": 2.0},
        60: {"name": "Roland-Garros", "mult": 1.8}
    },
    "Lyon": {
        20: {"name": "Fête des Lumières", "mult": 2.0},
        21: {"name": "Fête des Lumières", "mult": 2.0},
        50: {"name": "Salon Sirha", "mult": 1.7},
        80: {"name": "Nuits de Fourvière", "mult": 1.5}
    },
    "Nice": {
        12: {"name": "Carnaval de Nice", "mult": 1.9},
        13: {"name": "Carnaval de Nice", "mult": 1.9},
        40: {"name": "Festival de Cannes", "mult": 2.2},
        41: {"name": "Festival de Cannes", "mult": 2.2},
        70: {"name": "Jazz à Juan", "mult": 1.6}
    },
    "Marseille": {
        18: {"name": "Festival de la Chandeleur", "mult": 1.4},
        42: {"name": "OM - Match Européen", "mult": 1.8},
        65: {"name": "Fête de la Musique", "mult": 1.5}
    },
    "Autre": {
        20: {"name": "Salon Professionnel", "mult": 1.6},
        50: {"name": "Festival Local", "mult": 1.5},
        75: {"name": "Événement Sportif", "mult": 1.7}
    }
}


def generate_custom_data(hotel_name, stars, total_rooms, base_price, city):
    """Génère un jeu de données de simulation personnalisé basé sur les paramètres utilisateur."""

    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_simulate = 90
    review_score = min(10.0, 5.5 + stars * 0.8 + random.uniform(-0.3, 0.3))

    compset = COMPSET_TEMPLATES.get(stars, COMPSET_TEMPLATES[3])
    events = CITY_EVENTS.get(city, CITY_EVENTS["Autre"])

    records = []

    for day in range(days_to_simulate):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")

        is_weekend = current_date.weekday() in [4, 5]
        weekend_multiplier = 1.3 if is_weekend else 1.0

        event_info = events.get(day, {"name": "Non", "mult": 1.0})
        event_multiplier = event_info["mult"]

        seasonality = 1.0 + (day / days_to_simulate) * 0.2
        market_multiplier = weekend_multiplier * event_multiplier * seasonality

        # CompSet
        compset_prices = []
        for comp_name, stats in compset.items():
            pos_price_factor = stats[0]
            comp_review = stats[1]

            daily_noise = random.uniform(0.95, 1.05)
            final_price = base_price * market_multiplier * pos_price_factor * daily_noise
            final_price = round(final_price, 2)
            compset_prices.append(final_price)

            market_occ = min(0.98, random.uniform(0.6, 0.90) * (market_multiplier / 1.2))

            records.append({
                "Date": date_str,
                "Hotel": comp_name,
                "Is_Compset": True,
                "Price": final_price,
                "Occupancy_Rate": round(market_occ, 2),
                "Rooms_Sold": int(total_rooms * market_occ),
                "Review_Score": comp_review,
                "Event": event_info["name"]
            })

        # Notre hôtel
        market_average = round(sum(compset_prices) / len(compset_prices), 2)

        if event_multiplier > 1.0:
            our_price = market_average * 0.85
            our_occ = 0.98
            rooms_sold_ly = int(total_rooms * 0.85)
        elif is_weekend:
            our_price = market_average * random.uniform(0.98, 1.02)
            our_occ = 0.85
            rooms_sold_ly = int(total_rooms * 0.80)
        else:
            our_price = market_average * 1.15
            our_occ = 0.55
            rooms_sold_ly = int(total_rooms * 0.65)

        our_price = round(our_price, 2)
        rooms_sold = int(total_rooms * our_occ)
        pickup_7d = int(random.uniform(0, rooms_sold * 0.3)) if day > 7 else random.randint(1, 5)
        no_show_rate = round(random.uniform(0.01, 0.08), 2)

        records.append({
            "Date": date_str,
            "Hotel": hotel_name,
            "Is_Compset": False,
            "Price": our_price,
            "Occupancy_Rate": round(our_occ, 2),
            "Rooms_Sold": rooms_sold,
            "Rooms_Sold_LY": rooms_sold_ly,
            "Pickup_7d": pickup_7d,
            "Capacity": total_rooms,
            "No_Show_Rate": no_show_rate,
            "Review_Score": review_score,
            "RevPAR": round(our_price * our_occ, 2),
            "Market_Avg_Price": market_average,
            "ARI": round((our_price / market_average) * 100, 2),
            "Event": event_info["name"]
        })

    df = pd.DataFrame(records)
    return df
