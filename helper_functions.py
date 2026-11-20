import csv
from models import Offer
import os
import csv
from models import Traveller
import ast
# from logging import get_logger
from cust_logging import get_logger
from regex_patters import OFFER_ID_RE, TIME_RE, LUGGAGE_RE

from datetime import datetime
from exceptions import DataFileError, InvalidRecordError
import re

log = get_logger()
REJECTED_FILE = "rejected_offers.csv"

traveller_id_counter = 101

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

# def load_vaild_offers(filename="offers.csv"):

#     valid_offers = []
#     invalid_offers = []

#     with open(filename,mode="r",newline="",encoding="utf-8") as file:

#         reader = csv.DictReader(file)

#         for num, row in enumerate(reader,start=2):

#             try:
#                 offer_id = row["offer_id"].strip()
#                 company = row["company"].strip()
#                 destination = row["destination"].strip()
#                 travel_date = row["travel_date"].strip()
#                 departure_time = row["departure_time"].strip()
#                 arrival_time = row["arrival_time"].strip()
#                 luggage_allowance = row["luggage_allowance"].strip()

#                 if not all([
#                     offer_id,
#                     company,
#                     destination,
#                     travel_date,
#                     departure_time,
#                     arrival_time,
#                     luggage_allowance
#                 ]):
#                     raise ValueError("Empty mandatory field")

#                 duration_minutes = float(row["duration_minutes"])
#                 price_eur = float(row["price_eur"])
#                 transfers = int(row["transfers"])
#                 stops = int(row["stops"])
#                 available_seats = int(row["available_seats"])
#                 customer_rating = float(row["customer_rating"])
#                 environmental_score = int(row["environmental_score"])
#                 refund_advance_pct = float(row["refund_advance_pct"])
#                 refund_same_day_pct = float(row["refund_same_day_pct"])

#                 changeable = row["changeable"].strip().lower() == "true"
#                 refundable = row["refundable"].strip().lower() == "true"

#                 if price_eur <= 0:
#                     raise ValueError("Invalid price")

#                 if duration_minutes <= 0:
#                     raise ValueError("Invalid duration")

#                 if transfers < 0 or stops < 0:
#                     raise ValueError("Negative transfers or stops")

#                 if available_seats < 0:
#                     raise ValueError("Invalid available seats")

#                 if not 0 <= customer_rating <= 5:
#                     raise ValueError("Invalid customer rating")

#                 if not 0 <= environmental_score <= 100:
#                     raise ValueError("Invalid environmental score")

#                 if not (0 <= refund_advance_pct <= 100 and 0 <= refund_same_day_pct <= 100):
#                     raise ValueError("Refund percentage outside 0-100")

#                 if refund_same_day_pct > refund_advance_pct:
#                     raise ValueError("Same-day refund higher than advance refund")

#                 if not refundable and (refund_advance_pct or refund_same_day_pct):
#                     raise ValueError("Non-refundable fare with a refund percentage")

#                 # 5. Create Offer object
#                 offer = Offer(
#                     offer_id=offer_id,
#                     company=company,
#                     destination=destination,
#                     travel_date=travel_date,
#                     departure_time=departure_time,
#                     duration_minutes=duration_minutes,
#                     arrival_time=arrival_time,
#                     price_eur=price_eur,
#                     transfers=transfers,
#                     luggage_allowance=luggage_allowance,
#                     changeable=changeable,
#                     refundable=refundable,
#                     available_seats=available_seats,
#                     customer_rating=customer_rating,
#                     environmental_score=environmental_score,
#                     stops=stops,
#                     refund_advance_pct=refund_advance_pct,
#                     refund_same_day_pct=refund_same_day_pct,
#                 )

#                 valid_offers.append(offer)

#             except (ValueError, TypeError, KeyError) as error:
#                 invalid_offers.append(row)
#                 print(f"Skipping row {num}: {error}")

#     print(f"\nData loading completed!")
#     print(f"Valid offers: {len(valid_offers)}")
#     print(f"Invalid offers: {len(invalid_offers)}")

#     return valid_offers

def _parse_bool(value, field):
    v = (value or "").strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    raise InvalidRecordError(f"'{field}' must be True/False, got {value!r}")


def load_vaild_offers(filename="offers.csv", known_companies=None, known_destinations=None):
    if not os.path.exists(filename):
        raise DataFileError(f"Offers file not found: {filename}")

    valid, rejected, corrected, sold_out = [], [], 0, 0

    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []

        for num, row in enumerate(reader, start=2):
            try:
                # ---- CORRECTED: formatting problems that need no guessing ----
                offer_id = row["offer_id"].strip().upper()
                company = row["company"].strip()
                destination = row["destination"].strip()
                travel_date = row["travel_date"].strip()
                departure_time = row["departure_time"].strip()
                arrival_time = row["arrival_time"].strip()
                raw_luggage = row["luggage_allowance"].strip()
                luggage_allowance = re.sub(r"\s+", " ", raw_luggage).lower()   # "2 Bags" -> "2 bags"
                if luggage_allowance != raw_luggage:
                    corrected += 1
                    log.info("Offers row %s corrected: luggage %r -> %r", num, raw_luggage, luggage_allowance)

                # ---- REJECTED: missing or impossible values ----
                if not all([offer_id, company, destination, travel_date,
                            departure_time, arrival_time, luggage_allowance]):
                    raise InvalidRecordError("empty mandatory field")
                if not OFFER_ID_RE.match(offer_id):
                    raise InvalidRecordError(f"invalid offer_id {offer_id!r}")
                if not (TIME_RE.match(departure_time) and TIME_RE.match(arrival_time)):
                    raise InvalidRecordError("departure/arrival time is not HH:MM")
                if not LUGGAGE_RE.match(luggage_allowance):
                    raise InvalidRecordError(f"invalid luggage {luggage_allowance!r}")
                datetime.strptime(travel_date, "%Y-%m-%d")          # ValueError = impossible date
                if known_companies is not None and company not in known_companies:
                    raise InvalidRecordError(f"unknown company {company!r}")
                if known_destinations is not None and destination not in known_destinations:
                    raise InvalidRecordError(f"unknown destination {destination!r}")

                duration_minutes = float(row["duration_minutes"])
                price_eur = float(row["price_eur"])
                transfers = int(row["transfers"])
                stops = int(row["stops"])
                available_seats = int(row["available_seats"])
                customer_rating = float(row["customer_rating"])
                environmental_score = int(row["environmental_score"])
                refund_advance_pct = float(row["refund_advance_pct"])
                refund_same_day_pct = float(row["refund_same_day_pct"])
                changeable = _parse_bool(row["changeable"], "changeable")
                refundable = _parse_bool(row["refundable"], "refundable")

                if price_eur <= 0:
                    raise InvalidRecordError(f"negative or zero price ({price_eur})")
                if duration_minutes <= 0:
                    raise InvalidRecordError(f"negative or zero duration ({duration_minutes})")
                if transfers < 0 or stops < 0:
                    raise InvalidRecordError("negative transfers or stops")
                if available_seats < 0:
                    raise InvalidRecordError("negative available seats")
                if not 0 <= customer_rating <= 5:
                    raise InvalidRecordError(f"rating {customer_rating} outside 0-5")
                if not 0 <= environmental_score <= 100:
                    raise InvalidRecordError("environmental score outside 0-100")

                # arrival must equal departure + duration (modulo 24 h, so overnight trips are fine)
                dep = int(departure_time[:2]) * 60 + int(departure_time[3:])
                arr = int(arrival_time[:2]) * 60 + int(arrival_time[3:])
                if (dep + round(duration_minutes)) % 1440 != arr:
                    raise InvalidRecordError("arrival time does not match departure + duration")

                if available_seats == 0:
                    sold_out += 1      # kept: valid data, but the filter hides it (no seats)

                valid.append(Offer(
                    offer_id=offer_id, company=company, destination=destination,
                    travel_date=travel_date, departure_time=departure_time,
                    duration_minutes=duration_minutes, arrival_time=arrival_time,
                    price_eur=price_eur, transfers=transfers,
                    luggage_allowance=luggage_allowance, changeable=changeable,
                    refundable=refundable, available_seats=available_seats,
                    customer_rating=customer_rating, environmental_score=environmental_score,
                    stops=stops, refund_advance_pct=refund_advance_pct,
                    refund_same_day_pct=refund_same_day_pct,
                ))

            except (InvalidRecordError, ValueError, TypeError, KeyError) as error:
                # ---- SET ASIDE for review, with the reason ----
                rejected.append({"source_row": num, "reason": f"{type(error).__name__}: {error}", **row})
                log.warning("Offers row %s rejected: %s", num, error)

    if rejected:
        with open(REJECTED_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source_row", "reason"] + columns,
                                    extrasaction="ignore", restval="")
            writer.writeheader()
            writer.writerows(rejected)

    log.info("Offers loaded: %d valid (%d corrected, %d with no seats), %d rejected -> %s",
             len(valid), corrected, sold_out, len(rejected), REJECTED_FILE)

    if not valid:
        raise DataFileError(f"No valid offers could be loaded from {filename}")
    return valid


def generate_traveller_id(name):
    """Next ID based on how many travellers are already saved (survives reruns)."""
    count = 0
    if os.path.exists(TRAVELER_FILE):
        with open(TRAVELER_FILE, newline="", encoding="utf-8") as f:
            count = sum(1 for _ in csv.DictReader(f))
    return f"{name.strip()}-{101 + count}"

TRAVELER_FILE = "travelers.csv"


def save_traveller(traveller: Traveller):
    """Appends a new traveller profile to travelers.csv with clean preference formatting."""
    file_exists = os.path.exists(TRAVELER_FILE)
    fieldnames = ["id","name", "age", "gender", "phone", "email", "type", "mandatory_preferences"]
    
    data = traveller.getDetails()
    # Ensure mandatory_preferences is stored cleanly as a pipe-separated string (e.g. "company|price_eur")
    if isinstance(data["mandatory_preferences"], list):
        data["mandatory_preferences"] = "|".join(data["mandatory_preferences"])

    with open(TRAVELER_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)



def load_travellers() -> dict:
    """Loads all saved travellers from travelers.csv and safely parses mandatory preferences."""
    travellers_dict = {}
    
    if not os.path.exists(TRAVELER_FILE):
        default_traveller = Traveller(
            id=f"Raol-{101}",
            name="Raol", age=24, gender="M", phone="94324303", 
            email="raol@gmail.com", traveller_type="Business",
            mandatory_preferences=["company", "price_eur", "transfers", "duration_minutes"]
        )
        save_traveller(default_traveller)

    with open(TRAVELER_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_prefs = row.get("mandatory_preferences", "")
            
            # Safe Parsing of the preferences string
            parsed_prefs = []
            if raw_prefs:
                try:
                    # 1. Try safe evaluation if it looks like a Python list representation (e.g. "['company']")
                    evaluated = ast.literal_eval(raw_prefs)
                    if isinstance(evaluated, list):
                        # Flatten or clean up nested items if necessary
                        for item in evaluated:
                            if isinstance(item, str) and item.startswith("[") and item.endswith("]"):
                                nested = ast.literal_eval(item)
                                parsed_prefs.extend(nested if isinstance(nested, list) else [str(nested)])
                            else:
                                parsed_prefs.append(str(item))
                    elif isinstance(evaluated, str):
                        parsed_prefs = [evaluated]
                except (ValueError, SyntaxError):
                    # 2. Fallback: Split by pipe '|' or commas if stored as a delimited string
                    if "|" in raw_prefs:
                        parsed_prefs = [p.strip() for p in raw_prefs.split("|") if p.strip()]
                    else:
                        # Clean up brackets/quotes manually
                        cleaned = raw_prefs.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                        parsed_prefs = [p.strip() for p in cleaned.split(",") if p.strip()]

            traveller = Traveller(
                id = row["id"],
                name=row["name"],
                age=int(row["age"]),
                gender=row["gender"],
                phone=row["phone"],
                email=row["email"],
                traveller_type=row["type"],
                mandatory_preferences=parsed_prefs
            )
            travellers_dict[traveller.name] = traveller

    return travellers_dict



def _policy(row, field, errors):
    """Reads '(90,20)' into (90.0, 20.0): (refund % before travel date, refund % on travel date)."""
    raw = (row.get(field) or "").strip()
    try:
        advance, same_day = [float(p) for p in raw.strip("()[] ").replace("|", ",").split(",")]
    except ValueError:
        errors.append(f"'{field}' must look like (90,20), got {raw!r}")
        return None
    return (advance, same_day)
    """Parses '(90,20)' into (90.0, 20.0) and validates it."""
    raw = (row.get(field) or "").strip()
    if not raw:
        errors.append(f"'{field}' is missing")
        return None
    parts = [p.strip() for p in raw.strip("()[] ").replace("|", ",").replace(";", ",").split(",")]
    if len(parts) != 2:
        errors.append(f"'{field}' must look like (90,20), got {raw!r}")
        return None
    try:
        advance, same_day = float(parts[0]), float(parts[1])
    except ValueError:
        errors.append(f"'{field}' must contain two numbers, got {raw!r}")
        return None
    if not (0 <= advance <= 100 and 0 <= same_day <= 100):
        errors.append(f"'{field}' percentages must be between 0 and 100, got {raw!r}")
        return None
    if same_day > advance:
        errors.append(f"'{field}': same-day refund ({same_day:g}%) cannot exceed advance refund ({advance:g}%)")
        return None
    return (advance, same_day)