
from models import Destination, BusCompany,Offer

import random
from datetime import datetime, timedelta
import csv

from helper_functions import calculate_env_score, load_vaild_offers

from constants import DESTINATIONS_PROFILE,BUS_COMPANIES
import re

bus_company_list=[
        "SolRuta",
        "CaminoExpress",
        "CostaLink",
        "VerdeBus",
        "NocheVia"
    ]

all_destinations_list = [
        "Barcelona", "Valencia", "Seville", "Malaga", "Granada",
        "Cordoba", "Bilbao", "San_Sebastian", "Zaragoza", "Alicante",
        "Murcia", "Salamanca", "Toledo", "Santiago_de_Compostela", "Cadiz"
    ]

fieldnames_list = [
        "offer_id", "company", "destination", "travel_date", "departure_time",
        "arrival_time", "duration_minutes", "price_eur", "transfers", "stops",
        "luggage_allowance", "changeable", "refundable", "available_seats",
        "customer_rating", "environmental_score"
        ]


coastal_destinations_list = ["Barcelona", "Valencia", "Seville", "Malaga", "Bilbao", "San_Sebastian", "Alicante", "Murcia", "Cadiz"]

major_cities_list = ["Barcelona", "Valencia", "Seville", "Malaga", "Zaragoza", "Bilbao"]

def create_automated_offers():


   

    current_date = datetime.now()
    # print(current_date)

    
    # defining the nature of destinations
   
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


            company = random.choice(bus_company_list)
            company = BUS_COMPANIES[company]

            if company.name == "CostaLink":
                dest = random.choice(coastal_destinations_list)
                dest = DESTINATIONS_PROFILE[dest]
            elif company.name == "CaminoExpress":
                dest = random.choice(major_cities_list)
                dest = DESTINATIONS_PROFILE[dest]
            else:
                dest = random.choice(all_destinations_list)
                dest = DESTINATIONS_PROFILE[dest]

            anomaly_chance = random.random()
            transfers =  0 if company.direct_route else random.choice([1,2,3])
            stops = 0 if company.direct_route else random.choice([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])

            if anomaly_chance < 0.02:
                price = company.price_per_km * dest.distance_km * -1
                
            else:
                price = company.price_per_km * dest.distance_km
                

            if anomaly_chance<0.1:
                duration = (dest.distance_km/company.bus_avg_speed) * -1
            else:
                duration = round(dest.distance_km/company.bus_avg_speed)

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


        # writing into csv file
        with open("offers.csv",mode="w",newline="",encoding="utf-8") as f:
            writter = csv.DictWriter(f,fieldnames=fieldnames_list)
            writter.writeheader()
            writter.writerows(offers_data)


    return load_vaild_offers()


            



            



