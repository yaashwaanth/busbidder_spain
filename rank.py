from helper_functions import get_field, normalize

DEFAULT_PREFERENCES = [
    "price_eur", "duration_minutes", "departure_time",
    "environmental_score", "stops",
]

# score keys used in the scores dict
PREFERENCE_ALIASES = {
    "max_luggage": "luggage_allowance",
    "luggage": "luggage_allowance",
    "preferred_company": "company",
    "budget": "price_eur",
    "max_duration": "duration_minutes",
    "max_transfers": "transfers",
    "max_stops": "stops",
    "flexibility": "changeable",
}

# "Night" crosses midnight, so it is handled separately below.
TIME_WINDOWS = {
    "Morning": ("05:00", "11:59"),
    "AfterNoon": ("12:00", "16:59"),
    "Evening": ("17:00", "19:59"),
    "Night": ("20:00", "04:59"),
}
WINDOW_ORDER = ["Morning", "AfterNoon", "Evening", "Night"]


def resolve_preferences(trip_request):
    """Returns the list of score keys that count in the total score.
    Also useful for explain.py so both files use the same list."""
    traveller = getattr(trip_request, "traveller", trip_request)
    prefs = list(getattr(traveller, "mandatory_preferences", []) or [])

    prefs = [PREFERENCE_ALIASES.get(p, p) for p in prefs]

    # print(prefs)

    # remove duplicates, keep order
    prefs = list(dict.fromkeys(prefs))
    return prefs or list(DEFAULT_PREFERENCES)


def get_time_window(time_str: str) -> str:
    """Maps 'HH:MM' to Morning / AfterNoon / Evening / Night."""
    for name, (start, end) in TIME_WINDOWS.items():
        if start <= end:
            in_window = start <= time_str <= end
        else:  # window crosses midnight (Night)
            in_window = time_str >= start or time_str <= end
        if in_window:
            # print(in_window)
            return name
    return "Morning"





def evaluate_departure_time(preferred_departure: str, offer_time: str) -> float:
    """100 if inside the preferred window, minus 20 per window of distance.
    Windows are treated as a circle (Night is next to Morning)."""
    if preferred_departure not in WINDOW_ORDER:
        return 100.0  # no valid preference given, don't penalise

    offer_window = get_time_window(str(offer_time))
    diff = abs(WINDOW_ORDER.index(offer_window) - WINDOW_ORDER.index(preferred_departure))

    diff = min(diff, len(WINDOW_ORDER) - diff)  # circular distance
    print("diff->")
    # print(100.0-diff*20.0)
    return 100.0 - diff * 20.0

def _bag_count(text, default=1) -> int:
    try:
        return int(str(text).strip().split()[0])
    except (ValueError, IndexError):
        return default

def evaluate_luggage(offer_luggage, required_luggage) -> float:
    if not required_luggage:
        return 100.0
    return 100.0 if _bag_count(offer_luggage) >= _bag_count(required_luggage) else 50.0

def evaluate_company(offer_company, preferred_company) -> float:
    """100 for the preferred company, 70 for others. No preference = 100 for all."""
    if not preferred_company or preferred_company == "None":
        return 100.0
    return 100.0 if offer_company == preferred_company else 70.0

def rank_offers(offers, trip_request):
    """Ranks filtered offers with equal-weight scoring over the traveller's
    selected preferences. Scores are normalised across the offers passed in,
    so they are relative to this set, not absolute."""
    if not offers:
        return []


    def column(key, default):
        return [float(get_field(o, key, default)) for o in offers]

    prices = column("price_eur", 0)
    # print(prices)
    durations = column("duration_minutes", 0)
    environments = column("environmental_score", 50)
    stops_list = column("stops", 0)


    transfers_list = column("transfers", 0)
    ratings = column("customer_rating", 4.0)
    # print(ratings)

    min_price, max_price = min(prices), max(prices)
    min_dur, max_dur = min(durations), max(durations)
    min_env, max_env = min(environments), max(environments)
    min_stops, max_stops = min(stops_list), max(stops_list)
    min_transfers, max_transfers = min(transfers_list), max(transfers_list)
    min_rating, max_rating = min(ratings), max(ratings)

    selected_preferences = resolve_preferences(trip_request)

    preferred_departure = getattr(trip_request, "prefered_departure", "Morning")
    start_date = getattr(trip_request, "travel_start_date", "")
    required_luggage = getattr(trip_request, "max_luggage", "1 bags")
    preferred_company = getattr(trip_request, "preferred_company", "None")

    scored_offers = []

    for o in offers:
        # 1. normalised score (0-100) for every available attribute
        scores = {
            "price_eur": normalize(float(get_field(o, "price_eur", 0)), min_price, max_price, lower_better=True),
            "duration_minutes": normalize(float(get_field(o, "duration_minutes", 0)), min_dur, max_dur, lower_better=True),
            "environmental_score": normalize(float(get_field(o, "environmental_score", 50)), min_env, max_env, lower_better=False),
            "stops": normalize(float(get_field(o, "stops", 0)), min_stops, max_stops, lower_better=True),
            "transfers": normalize(float(get_field(o, "transfers", 0)), min_transfers, max_transfers, lower_better=True),
            "customer_rating": normalize(float(get_field(o, "customer_rating", 4.0)), min_rating, max_rating, lower_better=False),

            "departure_time": evaluate_departure_time(preferred_departure, get_field(o, "departure_time", "08:00")),
            "travel_date": 100.0 if start_date == get_field(o, "travel_date", "") else 60.0,

            "changeable": 100.0 if get_field(o, "changeable", False) else 0.0,
            "refundable": 100.0 if get_field(o, "refundable", False) else 0.0,

            "luggage_allowance": evaluate_luggage(get_field(o, "luggage_allowance", "1 bags"), required_luggage),
            "company": evaluate_company(get_field(o, "company", ""), preferred_company),
        }


        # print("scored_offers -> ")
        # print(scored_offers)

        # 2. equal-weight total over the selected preferences only
        valid_prefs = [p for p in selected_preferences if p in scores]

        if valid_prefs:
            total_score = sum(scores[p] for p in valid_prefs) / len(valid_prefs)
        else:
            total_score = 50.0







        # 3. attach results to the offer
        if isinstance(o, dict):
            o["criterion_scores"] = scores
            o["total_score"] = round(total_score, 1)
        else:
            o.criterion_scores = scores
            o.total_score = round(total_score, 1)

        scored_offers.append(o)

    # 4. highest score first; ties broken by cheaper price, then shorter duration
    scored_offers.sort(
        key=lambda x: (
            -float(get_field(x, "total_score", 0)),
            float(get_field(x, "price_eur", 0)),
            float(get_field(x, "duration_minutes", 0)),
        )
    )
    return scored_offers