from models import BusCompany, Destination
from data import load_destinations,load_bus_companies

# BUS_COMPANIES = {
#     "SolRuta": BusCompany(
#         name="SolRuta", 
#         bus_code="SOL",
#         price_per_km=0.050, 
#         speed_multiplier=1.10, 
#         co2_g_per_km=32,
#         departure_window=("06:00", "14:00"),
#         direct_route=False, 
#         coastal_focus=False, 
#         new_fleet=False,
#         budget_company=True,
#         bus_avg_speed=50
#     ),
#     "CaminoExpress": BusCompany(
#         name="CaminoExpress", 
#         bus_code="CAE",
#         price_per_km=0.075, 
#         speed_multiplier=0.90, 
#         co2_g_per_km=26,
#         departure_window=("11:00", "20:00"),
#         direct_route=True, 
#         coastal_focus=False, 
#         new_fleet=True,
#         budget_company=False,
#         bus_avg_speed = 85
#     ),
#     "CostaLink": BusCompany(
#         name="CostaLink", 
#         bus_code="COL",
#         price_per_km=0.062, 
#         speed_multiplier=1.05, 
#         co2_g_per_km=28,
#         departure_window=("16:00", "20:00"),
#         direct_route=False, 
#         coastal_focus=True, 
#         new_fleet=False,
#         budget_company=False,
#         bus_avg_speed = 60
#     ),
#     "VerdeBus": BusCompany(
#         name="VerdeBus", bus_code="VDB",
#         price_per_km=0.071, 
#         speed_multiplier=1.00,
#         co2_g_per_km=18,
#         departure_window=("16:30", "23:00"),
#         direct_route=False, 
#         coastal_focus=False, 
#         new_fleet=True,
#         budget_company=False,
#         bus_avg_speed = 62
#     ),
#     "NocheVia": BusCompany(
#         name="NocheVia", 
#         bus_code="NOV",
#         price_per_km=0.059, 
#         speed_multiplier=1.05, 
#         co2_g_per_km=29,
#         departure_window=("15:30", "23:59"),
#         direct_route=False, 
#         coastal_focus=False, 
#         new_fleet=False,
#         budget_company=False,
#         bus_avg_speed = 80
#     ),
# }

# DESTINATIONS_PROFILE = {
#     "Barcelona": Destination(
#         name="Barcelona", costal=True, major_city=True,
#         distance_km=620, base_duration_min=420, base_price_eur=38),
#     "Valencia": Destination(
#         name="Valencia", costal=True, major_city=True,
#         distance_km=355, base_duration_min=255, base_price_eur=22),
#     "Seville": Destination(
#         name="Seville", costal=False, major_city=True,
#         distance_km=530, base_duration_min=360, base_price_eur=32),
#     "Malaga": Destination(
#         name="Malaga", costal=True, major_city=True,
#         distance_km=530, base_duration_min=390, base_price_eur=33),
#     "Granada": Destination(
#         name="Granada", costal=False, major_city=False,
#         distance_km=430, base_duration_min=330, base_price_eur=28),
#     "Cordoba": Destination(
#         name="Cordoba", costal=False, major_city=True,
#         distance_km=400, base_duration_min=255, base_price_eur=24),
#     "Bilbao": Destination(
#         name="Bilbao", costal=True, major_city=True,
#         distance_km=400, base_duration_min=300, base_price_eur=29),
#     "San_Sebastian": Destination(
#         name="San Sebastian", costal=True, major_city=False,
#         distance_km=470, base_duration_min=330, base_price_eur=32),
#     "Zaragoza": Destination(
#         name="Zaragoza", costal=False, major_city=True,
#         distance_km=320, base_duration_min=225, base_price_eur=19),
#     "Alicante": Destination(
#         name="Alicante", costal=True, major_city=True,
#         distance_km=420, base_duration_min=330, base_price_eur=27),
#     "Murcia": Destination(
#         name="Murcia", costal=True, major_city=True,
#         distance_km=400, base_duration_min=330, base_price_eur=28),
#     "Salamanca": Destination(
#         name="Salamanca", costal=False, major_city=False,
#         distance_km=210, base_duration_min=150, base_price_eur=14),
#     "Toledo": Destination(
#         name="Toledo", costal=False, major_city=False,
#         distance_km=70, base_duration_min=60, base_price_eur=6),
#     "Santiago_de_Compostela": Destination(
#         name="Santiago de Compostela", costal=False, major_city=False,
#         distance_km=600, base_duration_min=480, base_price_eur=42),
#     "Cadiz": Destination(
#         name="Cadiz", costal=True, major_city=False,
#         distance_km=650, base_duration_min=480, base_price_eur=40),
# }


BUS_COMPANIES  = load_bus_companies()

DESTINATIONS_PROFILE = load_destinations()