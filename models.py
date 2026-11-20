

class Traveller:
    def __init__(self,id, name, age, gender,phone, email,traveller_type,mandatory_preferences):
        self.id = id
        self.name = name
        self.age = age
        self.email = email
        self.gender = gender
        self.phone = phone
        self.traveller_type = traveller_type
        self.mandatory_preferences = mandatory_preferences #[price, duration, departure_time, environment, stops] only 5 parameters
    def getDetails(self):
        return {
            "id":self.id,
            "name": self.name,
            "age":self.age,
            "gender":self.gender,
            "phone":self.phone,
            "email":self.email,
            "type": self.traveller_type,
            "mandatory_preferences": self.mandatory_preferences

        }


class Destination:
    def __init__(self,name,costal,major_city,distance_km,base_duration_min,base_price_eur):
           self.name= name 
           self.costal =costal 
           self.majmajor_city= major_city
           self.distance_km=distance_km # distance from madrid
           self.base_duration_min = base_duration_min
           self.base_price_eur = base_price_eur


class BusCompany:
 def __init__(self,name, bus_code,price_per_km, co2_g_per_km,direct_route,new_fleet, departure_window,coastal_focus,budget_company,bus_avg_speed,cancellation_policy):
    self.name = name
    self.bus_code = bus_code
    self.price_per_km= price_per_km        # EUR per km
    self.co2_g_per_km=co2_g_per_km      # grams CO2 per passenger-km
    self.departure_window=departure_window    # ("HH:MM", "HH:MM"); may cross midnight
    self.direct_route= direct_route
    self.coastal_focus=coastal_focus
    self.new_fleet=new_fleet
    self.budget_company=budget_company
    self.bus_avg_speed = bus_avg_speed
    self.cancellation_policy = cancellation_policy



class Offer:
    def __init__(self,offer_id,company,destination,travel_date,departure_time,duration_minutes,arrival_time, price_eur, transfers,luggage_allowance, changeable,refundable, available_seats, customer_rating, environmental_score,stops,refund_advance_pct,refund_same_day_pct):
        self.offer_id = offer_id
        self.company = company #string
        self.destination = destination #string
        self.travel_date = travel_date #string
        self.departure_time = departure_time# string
        self.arrival_time = arrival_time#string
        self.duration_minutes= duration_minutes #float
        self.price_eur = price_eur #float
        self.transfers = transfers # int
        self.stops = stops #int
        self.luggage_allowance = luggage_allowance # string

        self.changeable = changeable #booloean
        self.refundable = refundable  #booloean
        self.available_seats = available_seats # int
        self.customer_rating = customer_rating #float
        self.environmental_score = environmental_score #int [0-100]
        self.refund_advance_pct = refund_advance_pct      
        self.refund_same_day_pct = refund_same_day_pct 



class Trip_Request:
    def __init__(self,traveller,destination,max_stops,travel_start_date,travel_end_date,budget,max_transfers,max_luggage,prefered_departure,max_duration,flexiblity,preferred_company):
        self.traveller = traveller # composition
        self.destination = destination
        self.travel_start_date = travel_start_date
        self.travel_end_date = travel_end_date
        self.budget=budget
        self.max_transfers = max_transfers
        self.max_luggage = max_luggage
        self.max_stops = max_stops
        self.max_duration = max_duration
        self.prefered_departure = prefered_departure # morning, afternoon, evening, night
        self.flexiblity = flexiblity
        self.preferred_company = preferred_company



class Booking:
    def __init__(self,booking_id,traveller,offer,fare_conditions):
        self.booking_id = booking_id
        self.traveller = traveller
        self.offer = offer
        self.fare_conditions = fare_conditions or {}
        self.cancellation_policy = (
            self.fare_conditions.get("refund_advance_pct", 0),
            self.fare_conditions.get("refund_same_day_pct", 0),
        )
    def getDetails(self):
        return {
            "booking_id": self.booking_id,
            "offer_id": self.offer_id,
            "traveller": self.traveller,
            **self.fare_conditions,
        }

