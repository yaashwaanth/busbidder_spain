import csv
import os
from models import BusCompany, Destination

from helper_functions import _policy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUS_COMPANIES_FILE =  os.path.join(BASE_DIR,"bus_companies.csv")


def to_bool(value:str) -> bool:
    return value.strip().lower() in ("true","1","yes")



def load_bus_companies(filename=BUS_COMPANIES_FILE) -> dict:
    companies={}
    with open(filename,newline="",encoding="utf-8")as f:
        for num, row in enumerate(csv.DictReader(f),start=2):
            try:
                errors =[]
                policy = _policy(row,"cancellation_policy",errors)

                if errors:
                    raise ValueError(";".join(errors))
                
                name = row["name"].strip()
                companies[name] = BusCompany(
                    name=name,
                    bus_code=row["bus_code"].strip(),
                    price_per_km=float(row["price_per_km"]),
                    co2_g_per_km= float(row["co2_g_per_km"]),
                    departure_window=(
                        row["departure_start"].strip(),
                        row["departure_end"].strip(),
                    ),
                    direct_route=to_bool(row["direct_route"]),
                    coastal_focus=to_bool(row["coastal_focus"]),
                    new_fleet=to_bool(row["new_fleet"]),
                    budget_company=to_bool(row["budget_company"]),
                    bus_avg_speed=float(row["bus_avg_speed"]),
                    cancellation_policy =policy

                )

    

            except (KeyError,ValueError) as error:
                print(f"Skipping bus company row {num}:{error}")
    print(companies)

    if not companies:
        raise ValueError(
            "No valid bus companies loaded from bus_companies.csv. "
            "Check the 'Skipping bus company row' messages above."
        )
    return  companies



DESTINATIONS_FILE = os.path.join(BASE_DIR,"destinations.csv")
def load_destinations(filename=DESTINATIONS_FILE) -> dict:
    destinations = {}

    with open(filename, newline="", encoding="utf-8") as f:
        for num, row in enumerate(csv.DictReader(f), start=2):
            try:
                key = row["key"].strip()
                destinations[key] = Destination(
                    name=row["name"].strip(),
                    costal=to_bool(row["costal"]),
                    major_city=to_bool(row["major_city"]),
                    distance_km=float(row["distance_km"]),
                    base_duration_min=float(row["base_duration_min"]),
                    base_price_eur=float(row["base_price_eur"]),
                )
            except (KeyError, ValueError) as error:
                print(f"Skipping destination row {num}: {error}")
    print(destinations)
    return destinations


# load_destinations()
load_bus_companies()