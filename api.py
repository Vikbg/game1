from fastapi import FastAPI
import requests
import re
import time
from functools import lru_cache

app = FastAPI()

NASA_HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

@lru_cache(maxsize=50)  # Cache jusqu'à 50 résultats pour éviter les requêtes répétées
def fetch_horizons_data(planet_id):
    """Récupère les données d'un corps céleste depuis Horizons"""
    
    params = {
        "format": "text",
        "COMMAND": f"'{planet_id}'",
        "OBJ_DATA": "YES",
        "EPHEM_TYPE": "VECTORS",
        "START_TIME": "2024-02-21",
        "STOP_TIME": "2024-02-22",
        "STEP_SIZE": "1d"
    }

    response = requests.get(NASA_HORIZONS_URL, params=params)

    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_data(text):
    """Extrait les informations utiles de la réponse Horizons"""
    
    name_match = re.search(r"Revised: .*? (.+?) \d+", text)
    radius_match = re.search(r"Vol\. Mean Radius km\s*=\s*([\d.]+)", text)
    mass_match = re.search(r"Mass x10\^24 kg=\s*([\d.]+)", text)
    position_match = re.search(r"X\s*=\s*([\d.E+-]+)\s*Y\s*=\s*([\d.E+-]+)\s*Z\s*=\s*([\d.E+-]+)", text)
    velocity_match = re.search(r"VX\s*=\s*([\d.E+-]+)\s*VY\s*=\s*([\d.E+-]+)\s*VZ\s*=\s*([\d.E+-]+)", text)
    albedo_match = re.search(r"Geometric albedo\s*=\s*([\d.]+)", text)
    temp_match = re.search(r"Mean surface temp Ts, K=\s*([\d.]+)", text)

    return {
        "name": name_match.group(1) if name_match else "Unknown",
        "radius_km": float(radius_match.group(1)) if radius_match else None,
        "mass_10^24_kg": float(mass_match.group(1)) if mass_match else None,
        "position_km": {
            "x": float(position_match.group(1)) if position_match else None,
            "y": float(position_match.group(2)) if position_match else None,
            "z": float(position_match.group(3)) if position_match else None,
        },
        "velocity_km_s": {
            "vx": float(velocity_match.group(1)) if velocity_match else None,
            "vy": float(velocity_match.group(2)) if velocity_match else None,
            "vz": float(velocity_match.group(3)) if velocity_match else None,
        },
        "albedo": float(albedo_match.group(1)) if albedo_match else None,
        "temperature_K": float(temp_match.group(1)) if temp_match else None
    }

@app.get("/planet/{planet_id}")
def get_planet_data(planet_id: int):
    """Renvoie les données formatées d'un corps céleste"""

    raw_data = fetch_horizons_data(planet_id)

    if raw_data:
        data = extract_data(raw_data)
        return data
    else:
        return {"error": "Impossible de récupérer les données"}

@app.get("/planets/")
def get_multiple_planets(planet_ids: str):
    """Permet de récupérer plusieurs corps célestes en une seule requête.
       Exemple : /planets/?planet_ids=399,301,599
    """
    planet_ids_list = planet_ids.split(",")
    results = {}

    for planet_id in planet_ids_list:
        raw_data = fetch_horizons_data(int(planet_id))
        if raw_data:
            results[planet_id] = extract_data(raw_data)
        else:
            results[planet_id] = {"error": "Données indisponibles"}

    return results