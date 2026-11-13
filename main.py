import csv
from models import Traveller, Trip_Request, Offer,Booking
from offers import create_automated_offers
from filter import filter_offers
from rank import rank_offers


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