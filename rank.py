from helper_functions import get_field, normalize


def evaluate_departure_time(prefered_departure: str,offer_time:int) -> float:

    time_windows = {
        "Morning": ("05:00","11:59"),
        "AfterNoon": ("12:00","16:59"),
        "Evening": ("17:00","19:59"),
        "Night":("20:00","04:59")
    }
    
    rank = {
        "Morning": 1,
        "AfterNoon":2 ,
        "Evening": 3,
        "Night": 4
    }

    offer_time_window = "Morning" # default

    for name,(start,end) in time_windows.items():
        if offer_time>= start and offer_time<= end:
            offer_time_window = name

    return 100.0 - float((abs(rank[offer_time_window] - rank[prefered_departure]) *20)
)




def evaluate_luggage(offer_luggage:str, required_luggage:str) -> float:
    if not required_luggage:
        return 100.0

    try:
        off_count = int(str(offer_luggage).strip().split()[0])
    except (ValueError,IndexError):
        off_count = 1

    try:
        req_count = int(str(required_luggage).strip().split()[0])
    except (ValueError,IndexError):
        req_count =1

    if off_count >=req_count:
        return 100.0
    return 50.0

def rank_offers(offers, trip_request):
    """Ranks filtered offers using multi-criteria weighted scoring powered by the normalize function."""
    if not offers:
        return []

    # Extract boundaries for metrics
    prices = [float(get_field(o, 'price_eur', 0)) for o in offers]
    durations = [float(get_field(o, 'duration_minutes', 0)) for o in offers]
    environments = [float(get_field(o, 'environmental_score', 50)) for o in offers]
    stops_list = [float(get_field(o, 'stops', 0)) for o in offers]
    transfers_list = [float(get_field(o, 'transfers', 0)) for o in offers]
    ratings_list = [float(get_field(o, 'customer_rating', 4.0)) for o in offers]

    min_price, max_price = min(prices), max(prices)
    min_dur, max_dur = min(durations), max(durations)
    min_env, max_env = min(environments), max(environments)
    min_stops, max_stops = min(stops_list), max(stops_list)
    min_transfers, max_transfers = min(transfers_list), max(transfers_list)
    min_rating, max_rating = min(ratings_list), max(ratings_list)


    traveller_obj = getattr(trip_request, "traveller", trip_request)
    selected_preferences = getattr(traveller_obj, "mandatory_preferences", [])

    if not selected_preferences:
        selected_preferences = ["price_eur", "duration_minutes", "departure_time", "environmental_score", "stops"]

    scored_offers = []

    for o in offers:
        # 3. Pre-compute normalized scores for all available offer attributes
        scores = {
            "price_eur": normalize(float(get_field(o, 'price_eur', 0)), min_price, max_price, lower_better=True),
            "duration_minutes": normalize(float(get_field(o, 'duration_minutes', 0)), min_dur, max_dur, lower_better=True),
            
            "environmental_score": normalize(float(get_field(o, 'environmental_score', 50)), min_env, max_env, lower_better=False),
            "stops": normalize(float(get_field(o, 'stops', 0)), min_stops, max_stops, lower_better=True),
            
            "transfers": normalize(float(get_field(o, 'transfers', 0)), min_transfers, max_transfers, lower_better=True),
            
            # Customer Rating (Higher is better)
            "customer_rating": normalize(float(get_field(o, 'customer_rating', 4.0)), min_rating, max_rating, lower_better=False),
            
            # Departure Time & Date
            "departure_time": evaluate_departure_time(getattr(trip_request, "prefered_departure", "Morning"), get_field(o, 'departure_time', "08:00")),
            "travel_date": 100.0 if getattr(trip_request, "travel_start_date", "") == get_field(o, 'travel_date', "") else 60.0,
            
            # Booleans (True = 100.0, False = 0.0)
            "changeable": 100.0 if get_field(o, 'changeable', False) else 0.0,
            
            "refundable": 100.0 if get_field(o, 'refundable', False) else 0.0,
            
            # Categorical / Text fields
            "luggage_allowance": evaluate_luggage(get_field(o, 'luggage_allowance', "1 piece"), getattr(trip_request, "max_luggage", "1 piece")),
            
            # Company matching/evaluation
            "company": 100.0 if get_field(o, 'company', '') == getattr(trip_request, "preferred_company", get_field(o, 'company', '')) else 70.0,
        }

        # 4. Dynamic Calculation using ONLY keys present in the user's array
        valid_prefs = [p for p in selected_preferences if p in scores]
        print("ranking ->" )
        print(valid_prefs)



        if valid_prefs:
            weight_per_pref = 1.0 / len(valid_prefs)
            
            total_score = sum(scores[pref] * weight_per_pref for pref in valid_prefs)
        else:
            total_score = 50.0

        # some = 
        # weight_per_pref_all = 1.0 / len()
        # total_score_all = 

        # Attach computed metadata
        if isinstance(o, dict):
            o["criterion_scores"] = scores
           
            o["total_score"] = round(total_score, 1)
        else:
            o.criterion_scores = scores
            
            o.total_score = round(total_score, 1)
            
        scored_offers.append(o)

    # 5. Sort descending so the highest-scoring offer ranks first (#1)
    if isinstance(offers[0], dict):
        scored_offers.sort(key=lambda x: x["total_score"], reverse=True)
    else:
        scored_offers.sort(key=lambda x: x.total_score, reverse=True)
        
    return scored_offers