class Destination:
    def __init__(self,name,costal,major_city,distance_km,base_duration_min,base_price_eur):
           self.name= name 
           self.costal =costal 
           self.majmajor_city= major_city
           self.distance_km=distance_km # distance from madrid
           self.base_duration_min = base_duration_min
           self.base_price_eur = base_price_eur


class BusCompany:
 def __init__(self,name, bus_code,price_per_km,speed_multiplier, co2_g_per_km,direct_route, departure_window,coastal_focus,new_fleet,budget_company):
    self.name = name
    self.bus_code = bus_code
    self.price_per_km= price_per_km        # EUR per km
    self.speed_multiplier=   speed_multiplier   # >1 = slower than average, <1 = faster
    self.co2_g_per_km=co2_g_per_km      # grams CO2 per passenger-km
    self.departure_window=departure_window    # ("HH:MM", "HH:MM"); may cross midnight
    self.direct_route= direct_route
    self.coastal_focus=coastal_focus
    self.new_fleet=new_fleet
  # 1-5 scale
     # basic luggage allowance

    self.budget_company=budget_company
