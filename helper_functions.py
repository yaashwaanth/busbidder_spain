import csv
from models import Offer

def calculate_env_score(company,destination):
    """
    This functions helps in calculating the environment score of the bus company to a particular destination.
    """

    # here we calculate total co2 release during a ride to particular destination in kg
    total_emission_kg = (company.co2_g_per_km * destination.distance_km)

    # Base emission penalty: lower emissions per km result in a higher base score.
    # Assuming standard bus emissions range roughly from 20g/km (ultra-green/electric) to 50g/km (older diesel).
    # We map this inversely to a 0-100 scale.
    max_expected_co2_per_km = 55.0
    min_expected_co2_per_km = 20.0


    # 
    clamped_co2 = max(min_expected_co2_per_km, min(company.co2_g_per_km, max_expected_co2_per_km))

    # lower co2 = higher score(0 to 100)
    base_score = ((max_expected_co2_per_km - clamped_co2) / (max_expected_co2_per_km - min_expected_co2_per_km)) * 100.0

    # if company uses new/modern fleet, will have bonus
    modern_fleet_bonus = 10.0 if company.new_fleet else 0.0

    #final score
    final_score = base_score + modern_fleet_bonus
    if(company.name == "VerdeBus"):
     print(final_score)
    return int(max(0.0,min(100.0,final_score)))




def get_field(obj, key, default=None):
    """Helper to safely retrieve values whether the offer is an object or a dictionary."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def normalize(value, min_val, max_val, lower_better=True):
    """Normalizes any metric onto a 0-100 scale."""
    if min_val == max_val:
        return 100.0

    if lower_better:
        score = ((max_val - value) / (max_val - min_val)) * 100.0
    else:
        score = ((value - min_val) / (max_val - min_val)) * 100.0

    return max(0.0, min(100.0, score))

def load_vaild_offers(filename="offers.csv"):

    valid_offers = []
    invalid_offers = []

    with open(filename,mode="r",newline="",encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for num, row in enumerate(reader,start=2):

            try:
                offer_id = row["offer_id"].strip()
                company = row["company"].strip()
                destination = row["destination"].strip()
                travel_date = row["travel_date"].strip()
                departure_time = row["departure_time"].strip()
                arrival_time = row["arrival_time"].strip()
                luggage_allowance = row["luggage_allowance"].strip()

                if not all([
                    offer_id,
                    company,
                    destination,
                    travel_date,
                    departure_time,
                    arrival_time,
                    luggage_allowance
                ]):
                    raise ValueError("Empty mandatory field")

                duration_minutes = float(row["duration_minutes"])
                price_eur = float(row["price_eur"])
                transfers = int(row["transfers"])
                stops = int(row["stops"])
                available_seats = int(row["available_seats"])
                customer_rating = float(row["customer_rating"])
                environmental_score = int(row["environmental_score"])

                changeable = row["changeable"].strip().lower() == "true"
                refundable = row["refundable"].strip().lower() == "true"

                if price_eur <= 0:
                    raise ValueError("Invalid price")

                if duration_minutes <= 0:
                    raise ValueError("Invalid duration")

                if transfers < 0 or stops < 0:
                    raise ValueError("Negative transfers or stops")

                if available_seats < 0:
                    raise ValueError("Invalid available seats")

                if not 0 <= customer_rating <= 5:
                    raise ValueError("Invalid customer rating")

                if not 0 <= environmental_score <= 100:
                    raise ValueError("Invalid environmental score")

                # 5. Create Offer object
                offer = Offer(
                    offer_id=offer_id,
                    company=company,
                    destination=destination,
                    travel_date=travel_date,
                    departure_time=departure_time,
                    duration_minutes=duration_minutes,
                    arrival_time=arrival_time,
                    price_eur=price_eur,
                    transfers=transfers,
                    luggage_allowance=luggage_allowance,
                    changeable=changeable,
                    refundable=refundable,
                    available_seats=available_seats,
                    customer_rating=customer_rating,
                    environmental_score=environmental_score,
                    stops=stops
                )

                valid_offers.append(offer)

            except (ValueError, TypeError, KeyError) as error:
                invalid_offers.append(row)
                print(f"Skipping row {num}: {error}")

    print(f"\nData loading completed!")
    print(f"Valid offers: {len(valid_offers)}")
    print(f"Invalid offers: {len(invalid_offers)}")

    return valid_offers
