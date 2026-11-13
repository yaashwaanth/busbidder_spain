
from models import Destination, BusCompany,Offer

import random
from datetime import datetime, timedelta
import csv

from helper_functions import calculate_env_score, load_vaild_offers

import re
bus_companies = {
    "SolRuta": BusCompany(
        name="SolRuta", 
        bus_code="SOL",
        price_per_km=0.050, 
        speed_multiplier=1.10, 
        co2_g_per_km=32,
        departure_window=("06:00", "14:00"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=False,
        budget_company=True
    ),
    "CaminoExpress": BusCompany(
        name="CaminoExpress", 
        bus_code="CAE",
        price_per_km=0.075, 
        speed_multiplier=0.90, 
        co2_g_per_km=26,
        departure_window=("11:00", "20:00"),
        direct_route=True, 
        coastal_focus=False, 
        new_fleet=True,
        budget_company=False
    ),
    "CostaLink": BusCompany(
        name="CostaLink", 
        bus_code="COL",
        price_per_km=0.062, 
        speed_multiplier=1.05, 
        co2_g_per_km=28,
        departure_window=("16:00", "20:00"),
        direct_route=False, 
        coastal_focus=True, 
        new_fleet=False,
        budget_company=False
    ),
    "VerdeBus": BusCompany(
        name="VerdeBus", bus_code="VDB",
        price_per_km=0.071, 
        speed_multiplier=1.00,
        co2_g_per_km=18,
        departure_window=("16:30", "23:00"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=True,
        budget_company=False
    ),
    "NocheVia": BusCompany(
        name="NocheVia", 
        bus_code="NOV",
        price_per_km=0.059, 
        speed_multiplier=1.05, 
        co2_g_per_km=29,
        departure_window=("15:30", "23:59"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=False,
        budget_company=False
    ),
}



def create_automated_offers():

    

    bus_company=[
        "SolRuta",
        "CaminoExpress",
        "CostaLink",
        "VerdeBus",
        "NocheVia"
    ]

    # destinations
    # destinations={
    #     "Barcelona", 
    #     "Valencia", 
    #     "Seville", 
    #     "Malaga", 
    #     "Granada",
    #     "Cordoba",
    #     "Bilbao", 
    #     "San Sebastian", 
    #     "Zaragoza", 
    #     "Alicante",
    #     "Murcia", 
    #     "Salamanca", 
    #     "Toledo", 
    #     "Santiago de Compostela", 
    #     "Cadiz"
    # }


    destinations = {
    "Barcelona": Destination(
        name="Barcelona", costal=True, major_city=True,
        distance_km=620, base_duration_min=420, base_price_eur=38),
    "Valencia": Destination(
        name="Valencia", costal=True, major_city=True,
        distance_km=355, base_duration_min=255, base_price_eur=22),
    "Seville": Destination(
        name="Seville", costal=False, major_city=True,
        distance_km=530, base_duration_min=360, base_price_eur=32),
    "Malaga": Destination(
        name="Malaga", costal=True, major_city=True,
        distance_km=530, base_duration_min=390, base_price_eur=33),
    "Granada": Destination(
        name="Granada", costal=False, major_city=False,
        distance_km=430, base_duration_min=330, base_price_eur=28),
    "Cordoba": Destination(
        name="Cordoba", costal=False, major_city=True,
        distance_km=400, base_duration_min=255, base_price_eur=24),
    "Bilbao": Destination(
        name="Bilbao", costal=True, major_city=True,
        distance_km=400, base_duration_min=300, base_price_eur=29),
    "San_Sebastian": Destination(
        name="San Sebastian", costal=True, major_city=False,
        distance_km=470, base_duration_min=330, base_price_eur=32),
    "Zaragoza": Destination(
        name="Zaragoza", costal=False, major_city=True,
        distance_km=320, base_duration_min=225, base_price_eur=19),
    "Alicante": Destination(
        name="Alicante", costal=True, major_city=True,
        distance_km=420, base_duration_min=330, base_price_eur=27),
    "Murcia": Destination(
        name="Murcia", costal=True, major_city=True,
        distance_km=400, base_duration_min=330, base_price_eur=28),
    "Salamanca": Destination(
        name="Salamanca", costal=False, major_city=False,
        distance_km=210, base_duration_min=150, base_price_eur=14),
    "Toledo": Destination(
        name="Toledo", costal=False, major_city=False,
        distance_km=70, base_duration_min=60, base_price_eur=6),
    "Santiago_de_Compostela": Destination(
        name="Santiago de Compostela", costal=False, major_city=False,
        distance_km=600, base_duration_min=480, base_price_eur=42),
    "Cadiz": Destination(
        name="Cadiz", costal=True, major_city=False,
        distance_km=650, base_duration_min=480, base_price_eur=40),
    }

    current_date = datetime.now()
    # print(current_date)

    all_destinations = [
        "Barcelona", "Valencia", "Seville", "Malaga", "Granada",
        "Cordoba", "Bilbao", "San_Sebastian", "Zaragoza", "Alicante",
        "Murcia", "Salamanca", "Toledo", "Santiago_de_Compostela", "Cadiz"
    ]
    # defining the nature of destinations
    coastal_destinations = ["Barcelona", "Valencia", "Seville", "Malaga", "Bilbao", "San_Sebastian", "Alicante", "Murcia", "Cadiz"]
    major_cities = ["Barcelona", "Valencia", "Seville", "Malaga", "Zaragoza", "Bilbao"]

    offers_data = []
    offers_data_class =[]
    offer_counter_code = 101

    random.seed(42) # for reproduciblity
    start_date = current_date


    # this program created offers for next 90 days(3 months)
    for days in range(90):
        current_day = start_date + timedelta(days=days)
        travel_date_str = current_day.strftime("%Y-%m-%d")

        # creates 15 offers per day of individual bus companies
        for _ in range(10):


            company = random.choice(bus_company)
            company = bus_companies[company]

            if company.name == "CostaLink":
                dest = random.choice(coastal_destinations)
                dest = destinations[dest]
            elif company.name == "CaminoExpress":
                dest = random.choice(major_cities)
                dest = destinations[dest]
            else:
                dest = random.choice(all_destinations)
                dest = destinations[dest]

            anomaly_chance = random.random()
            transfers =  0 if company.direct_route else random.choice([1,2,3])
            stops = 0 if company.direct_route else random.choice([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])

            if anomaly_chance < 0.02:
                price = company.price_per_km * dest.distance_km * -1
                
            else:
                price = company.price_per_km * dest.distance_km
                

            if anomaly_chance<0.1:
                duration = (dest.distance_km/60) * -1
            else:
                duration = dest.distance_km/60

            dep_time = f"{random.randint(int(company.departure_window[0].split(':')[0]), int(company.departure_window[1].split(':')[0])):02d}:{random.choice([0, 30]):02d}"
            dep_hour, dep_min = map(int, dep_time.split(":"))
            arr_total_mins = dep_hour * 60 + dep_min + duration * 60
            arr_hour = (arr_total_mins // 60) % 24
            arr_min = arr_total_mins % 60
            arr_time = f"{int(arr_hour):02d}:{int(arr_min):02d}"

            curr_offer = {
                "offer_id": f"{company.name[:2].upper()}-{offer_counter_code}",
                "company": "" if anomaly_chance<0.02 else company.name,
                "destination": dest.name,
                "travel_date": travel_date_str,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration_minutes": duration*60,
                "price_eur": price,
                "transfers": transfers,
                "stops": stops,  # Column tracking intermediate stops
                "luggage_allowance": random.choice(["2 bags", "3 bags","4 bags","5 bags"]),
                "changeable": random.choice([True, False]),
                "refundable": random.choice([True, False]),
                "available_seats": random.randint(2, 20),
                "customer_rating": round(random.uniform(3.5, 5.0), 1),
                "environmental_score": calculate_env_score(company=company,destination=dest)
            }
            offers_data.append(curr_offer)

            offers_data_class.append(Offer(offer_id=curr_offer["offer_id"],company=curr_offer["company"],
                                           destination = curr_offer["destination"], travel_date = curr_offer["travel_date"],departure_time = curr_offer["departure_time"],
                                           arrival_time = curr_offer["arrival_time"], duration_minutes = curr_offer["duration_minutes"],price_eur=curr_offer["price_eur"],transfers=curr_offer["transfers"],stops=curr_offer["stops"],luggage_allowance=curr_offer["luggage_allowance"],
                                           changeable = curr_offer["changeable"], refundable = curr_offer["refundable"], available_seats= curr_offer["available_seats"],customer_rating=curr_offer["customer_rating"],
                                           environmental_score = curr_offer["environmental_score"]
                                           ))
            offer_counter_code += 1


        fieldnames = [
        "offer_id", "company", "destination", "travel_date", "departure_time",
        "arrival_time", "duration_minutes", "price_eur", "transfers", "stops",
        "luggage_allowance", "changeable", "refundable", "available_seats",
        "customer_rating", "environmental_score"
        ]

        with open("offers.csv",mode="w",newline="",encoding="utf-8") as f:
            writter = csv.DictWriter(f,fieldnames=fieldnames)
            writter.writeheader()
            writter.writerows(offers_data)


    return load_vaild_offers()


            



            



