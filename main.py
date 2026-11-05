import csv


class Traveller:
    def __init__(self, name, age, gender,phone, email,traveller_type):
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.email = email
        self.traveller_type = traveller_type




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


class BusCompany:
    name: str
    bus_code: str
    price_per_km: float          # EUR per km
    speed_multiplier: float      # >1 = slower than average, <1 = faster
    co2_g_per_km: float          # grams CO2 per passenger-km
    departure_window: tuple      # ("HH:MM", "HH:MM"); may cross midnight
    direct_only: bool = False
    coastal_focus: bool = False
    new_fleet: bool = False
    rating: float = 4.0          # 1-5 scale
    luggage_kg: int = 15         # basic luggage allowance

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
        departure_window=("07:30", "14:00"),
        direct_only=False, 
        coastal_focus=False, 
        new_fleet=False,
    ),
    "CaminoExpress": BusCompany(
        name="CaminoExpress", 
        bus_code="CAE",
        price_per_km=0.075, 
        speed_multiplier=0.90, 
        co2_g_per_km=26,
        departure_window=("07:00", "16:00"),
        direct_only=True, 
        coastal_focus=False, 
        new_fleet=True,
    ),
    "CostaLink": BusCompany(
        name="CostaLink", 
        bus_code="COL",
        price_per_km=0.062, 
        speed_multiplier=1.05, 
        co2_g_per_km=28,
        departure_window=("08:00", "15:00"),
        direct_only=False, 
        coastal_focus=True, 
        new_fleet=False,
    ),
    "VerdeBus": BusCompany(
        name="VerdeBus", bus_code="VDB",
        price_per_km=0.071, 
        speed_multiplier=1.00,
        co2_g_per_km=18,
        departure_window=("06:30", "17:00"),
        direct_only=False, 
        coastal_focus=False, 
        new_fleet=True,
    ),
    "NocheVia": BusCompany(
        name="NocheVia", 
        bus_code="NOV",
        price_per_km=0.059, 
        speed_multiplier=1.05, 
        co2_g_per_km=29,
        departure_window=("21:30", "00:30"),
        direct_only=False, 
        coastal_focus=False, 
        new_fleet=False,
    ),
}