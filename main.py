import csv
from models import Traveller, Trip_Request, Offer,Booking
from offers import create_automated_offers
from filter import filter_offers
from rank import rank_offers
# bus comany profiles
# bus_companies = {
#     "SolRuta": BusCompany(
#         name="SolRuta", 
#         bus_code="SOL",
#         price_per_km=0.050, 
#         speed_multiplier=1.10, 
#         co2_g_per_km=32,
#         departure_window=("06:00", "14:00"),
#         direct_route=False, 
#         coastal_route=False, 
#         new_fleet=False,
#         budget_company=True
#     ),
#     "CaminoExpress": BusCompany(
#         name="CaminoExpress", 
#         bus_code="CAE",
#         price_per_km=0.075, 
#         speed_multiplier=0.90, 
#         co2_g_per_km=26,
#         departure_window=("11:00", "20:00"),
#         direct_only=True, 
#         coastal_focus=False, 
#         new_fleet=True,
#         budget_company=False
#     ),
#     "CostaLink": BusCompany(
#         name="CostaLink", 
#         bus_code="COL",
#         price_per_km=0.062, 
#         speed_multiplier=1.05, 
#         co2_g_per_km=28,
#         departure_window=("16:00", "20:00"),
#         direct_only=False, 
#         coastal_focus=True, 
#         new_fleet=False,
#         budget_company=False
#     ),
#     "VerdeBus": BusCompany(
#         name="VerdeBus", bus_code="VDB",
#         price_per_km=0.071, 
#         speed_multiplier=1.00,
#         co2_g_per_km=18,
#         departure_window=("16:30", "23:00"),
#         direct_only=False, 
#         coastal_focus=False, 
#         new_fleet=True,
#         budget_company=False
#     ),
#     "NocheVia": BusCompany(
#         name="NocheVia", 
#         bus_code="NOV",
#         price_per_km=0.059, 
#         speed_multiplier=1.05, 
#         co2_g_per_km=29,
#         departure_window=("15:30", "23:59"),
#         direct_only=False, 
#         coastal_focus=False, 
#         new_fleet=False,
#         budget_company=False
#     ),
# }



# Destinations profiles
# destinations = {
#     "Barcelona": Destination(
#         name="Barcelona", coastal=True, major_city=True,
#         distance_km=620, base_duration_min=420, base_price_eur=38),
#     "Valencia": Destination(
#         name="Valencia", coastal=True, major_city=True,
#         distance_km=355, base_duration_min=255, base_price_eur=22),
#     "Seville": Destination(
#         name="Seville", coastal=False, major_city=True,
#         distance_km=530, base_duration_min=360, base_price_eur=32),
#     "Malaga": Destination(
#         name="Malaga", coastal=True, major_city=True,
#         distance_km=530, base_duration_min=390, base_price_eur=33),
#     "Granada": Destination(
#         name="Granada", coastal=False, major_city=False,
#         distance_km=430, base_duration_min=330, base_price_eur=28),
#     "Cordoba": Destination(
#         name="Cordoba", coastal=False, major_city=True,
#         distance_km=400, base_duration_min=255, base_price_eur=24),
#     "Bilbao": Destination(
#         name="Bilbao", coastal=True, major_city=True,
#         distance_km=400, base_duration_min=300, base_price_eur=29),
#     "San Sebastian": Destination(
#         name="San Sebastian", coastal=True, major_city=False,
#         distance_km=470, base_duration_min=330, base_price_eur=32),
#     "Zaragoza": Destination(
#         name="Zaragoza", coastal=False, major_city=True,
#         distance_km=320, base_duration_min=225, base_price_eur=19),
#     "Alicante": Destination(
#         name="Alicante", coastal=True, major_city=True,
#         distance_km=420, base_duration_min=330, base_price_eur=27),
#     "Murcia": Destination(
#         name="Murcia", coastal=True, major_city=True,
#         distance_km=400, base_duration_min=330, base_price_eur=28),
#     "Salamanca": Destination(
#         name="Salamanca", coastal=False, major_city=False,
#         distance_km=210, base_duration_min=150, base_price_eur=14),
#     "Toledo": Destination(
#         name="Toledo", coastal=False, major_city=False,
#         distance_km=70, base_duration_min=60, base_price_eur=6),
#     "Santiago de Compostela": Destination(
#         name="Santiago de Compostela", coastal=False, major_city=False,
#         distance_km=600, base_duration_min=480, base_price_eur=42),
#     "Cadiz": Destination(
#         name="Cadiz", coastal=True, major_city=False,
#         distance_km=650, base_duration_min=480, base_price_eur=40),
# }


def main():
    print("=============BusBidder Spain================")


    # creating a traveller profile
    raol = Traveller(name="Raol",age=24,gender="M",phone="94324303",email="raol@gmail.com",traveller_type="Business",mandatory_preferences=["Company","price_eur","transfers","duration"])

    # creating trip request
    raol_trip_1 = Trip_Request(traveller=raol,destination="Cordoba",travel_start_date="2026-11-22",travel_end_date="2026-11-30",budget=100,max_duration=24,max_luggage="1 peices",max_transfers=3,prefered_departure="Morning",flexiblity=True)

    # get offers
    total_offers = create_automated_offers()
    # print(total_offers[0].company)

    filtered_offers = filter_offers(offers=total_offers,trip_request=raol_trip_1)
    print(filtered_offers)
    # rank the offers
    print(rank_offers(filtered_offers,raol_trip_1))


    print("==================END=======================")



if __name__ == "__main__":
    main()