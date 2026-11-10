import csv
import streamlit as st

class Traveller:
    def __init__(self, name, age, gender,phone, email,traveller_type):
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.email = email
        self.traveller_type = traveller_type
    def getDetails(self):
        return {
            "name": self.name,
            "age":self.age,
            "gender":self.gender,
            "phone":self.phone,
            "email":self.email,
            "type": self.traveller_type

        }




class Offer:
    def __init(self,company,origin,destination,travel_date,departure_time,arrival_time, duration, price, transfers,luggage_allowance, changeablity,refundablity, available_seats, customer_rating, environmental_measure,terms_and_conditions):
        self.company = company
        self.origin = origin
        self.destination = destination
        self.travel_date = travel_date
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.duration = duration
        self.price = price
        self.transfers = transfers
        self.luggage = self.luggage
        self.luggage_allowance = luggage_allowance
        self.changeablity = changeablity
        self.refundablity = refundablity
        self.available_seats = available_seats
        self.customer_rating = customer_rating
        self.environmental_measure = environmental_measure
        self.terms_and_conditions = terms_and_conditions



# Multiple inheritance
class Booking(Traveller,Offer):
    def __init__(self,traveller,offer):
        self.traveller = traveller
        self.offer = offer



def getDetails(self):
          return {
              "name": self.name,
              "age":self.age,
              "gender":self.gender,
              "phone":self.phone,
              "email":self.email,
              "type": self.traveller_type
  
          }



def create_user(name, age, gender,phone, email,traveller_type) -> Traveller:
   return Traveller(name, age, gender,phone,email,traveller_type)


def create_offer(company,origin,destination,travel_date,departure_time,arrival_time, duration, price, transfers,luggage_allowance, changeablity,refundablity, available_seats, customer_rating, environmental_measure,terms_and_conditions)->Offer:
    return Offer(company,origin,destination,travel_date,departure_time,arrival_time, duration, price, transfers,luggage_allowance, changeablity,refundablity, available_seats, customer_rating, environmental_measure,terms_and_conditions)


def book_ticket(traveller,offer)-> Booking:
    return Booking(traveller,offer)

# bus comany profiles
bus_companies = {
    "SolRuta": BusCompany(
        name="SolRuta", 
        bus_code="SOL",
        price_per_km=0.050, 
        speed_multiplier=1.10, 
        co2_g_per_km=32,
        departure_window=("06:00", "14:00"),
        direct_route=False, 
        coastal_route=False, 
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
        direct_only=True, 
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
        direct_only=False, 
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
        direct_only=False, 
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
        direct_only=False, 
        coastal_focus=False, 
        new_fleet=False,
        budget_company=False
    ),
}



# Destinations profiles
destinations = {
    "Barcelona": Destination(
        name="Barcelona", coastal=True, major_city=True,
        distance_km=620, base_duration_min=420, base_price_eur=38),
    "Valencia": Destination(
        name="Valencia", coastal=True, major_city=True,
        distance_km=355, base_duration_min=255, base_price_eur=22),
    "Seville": Destination(
        name="Seville", coastal=False, major_city=True,
        distance_km=530, base_duration_min=360, base_price_eur=32),
    "Malaga": Destination(
        name="Malaga", coastal=True, major_city=True,
        distance_km=530, base_duration_min=390, base_price_eur=33),
    "Granada": Destination(
        name="Granada", coastal=False, major_city=False,
        distance_km=430, base_duration_min=330, base_price_eur=28),
    "Cordoba": Destination(
        name="Cordoba", coastal=False, major_city=True,
        distance_km=400, base_duration_min=255, base_price_eur=24),
    "Bilbao": Destination(
        name="Bilbao", coastal=True, major_city=True,
        distance_km=400, base_duration_min=300, base_price_eur=29),
    "San Sebastian": Destination(
        name="San Sebastian", coastal=True, major_city=False,
        distance_km=470, base_duration_min=330, base_price_eur=32),
    "Zaragoza": Destination(
        name="Zaragoza", coastal=False, major_city=True,
        distance_km=320, base_duration_min=225, base_price_eur=19),
    "Alicante": Destination(
        name="Alicante", coastal=True, major_city=True,
        distance_km=420, base_duration_min=330, base_price_eur=27),
    "Murcia": Destination(
        name="Murcia", coastal=True, major_city=True,
        distance_km=400, base_duration_min=330, base_price_eur=28),
    "Salamanca": Destination(
        name="Salamanca", coastal=False, major_city=False,
        distance_km=210, base_duration_min=150, base_price_eur=14),
    "Toledo": Destination(
        name="Toledo", coastal=False, major_city=False,
        distance_km=70, base_duration_min=60, base_price_eur=6),
    "Santiago de Compostela": Destination(
        name="Santiago de Compostela", coastal=False, major_city=False,
        distance_km=600, base_duration_min=480, base_price_eur=42),
    "Cadiz": Destination(
        name="Cadiz", coastal=True, major_city=False,
        distance_km=650, base_duration_min=480, base_price_eur=40),
}


def main():
    print(bus_companies["SolRuta"])
