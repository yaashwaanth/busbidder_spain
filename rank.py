# from helper_functions import get_field, normalize

# DEFAULT_PREFERENCES = [
#     "price_eur", "duration_minutes", "departure_time",
#     "environmental_score", "stops",
# ]

# # score keys used in the scores dict
# PREFERENCE_ALIASES = {
#     "max_luggage": "luggage_allowance",
#     "luggage": "luggage_allowance",
#     "preferred_company": "company",
#     "budget": "price_eur",
#     "max_duration": "duration_minutes",
#     "max_transfers": "transfers",
#     "max_stops": "stops",
#     "flexibility": "changeable",
# }

# # "Night" crosses midnight, so it is handled separately below.
# TIME_WINDOWS = {
#     "Morning": ("05:00", "11:59"),
#     "AfterNoon": ("12:00", "16:59"),
#     "Evening": ("17:00", "19:59"),
#     "Night": ("20:00", "04:59"),
# }
# WINDOW_ORDER = ["Morning", "AfterNoon", "Evening", "Night"]


# def resolve_preferences(trip_request):
#     """Returns the list of score keys that count in the total score.
#     Also useful for explain.py so both files use the same list."""
#     traveller = getattr(trip_request, "traveller", trip_request)
#     prefs = list(getattr(traveller, "mandatory_preferences", []) or [])

#     prefs = [PREFERENCE_ALIASES.get(p, p) for p in prefs]

#     # print(prefs)

#     # remove duplicates, keep order
#     prefs = list(dict.fromkeys(prefs))
#     return prefs or list(DEFAULT_PREFERENCES)


# def get_time_window(time_str: str) -> str:
#     """Maps 'HH:MM' to Morning / AfterNoon / Evening / Night."""
#     for name, (start, end) in TIME_WINDOWS.items():
#         if start <= end:
#             in_window = start <= time_str <= end
#         else:  # window crosses midnight (Night)
#             in_window = time_str >= start or time_str <= end
#         if in_window:
#             # print(in_window)
#             return name
#     return "Morning"





# def evaluate_departure_time(preferred_departure: str, offer_time: str) -> float:
#     """100 if inside the preferred window, minus 20 per window of distance.
#     Windows are treated as a circle (Night is next to Morning)."""
#     if preferred_departure not in WINDOW_ORDER:
#         return 100.0  # no valid preference given, don't penalise

#     offer_window = get_time_window(str(offer_time))
#     diff = abs(WINDOW_ORDER.index(offer_window) - WINDOW_ORDER.index(preferred_departure))

#     diff = min(diff, len(WINDOW_ORDER) - diff)  # circular distance
#     # print("diff->")
#     # print(100.0-diff*20.0)
#     return 100.0 - diff * 20.0

# def _bag_count(text, default=1) -> int:
#     try:
#         return int(str(text).strip().split()[0])
#     except (ValueError, IndexError):
#         return default

# def evaluate_luggage(offer_luggage, required_luggage) -> float:
#     if not required_luggage:
#         return 100.0
#     return 100.0 if _bag_count(offer_luggage) >= _bag_count(required_luggage) else 50.0

# def evaluate_company(offer_company, preferred_company) -> float:
#     """100 for the preferred company, 70 for others. No preference = 100 for all."""
#     if not preferred_company or preferred_company == "None":
#         return 100.0
#     return 100.0 if offer_company == preferred_company else 70.0

# def rank_offers(offers, trip_request):
#     """Ranks filtered offers with equal-weight scoring over the traveller's
#     selected preferences. Scores are normalised across the offers passed in,
#     so they are relative to this set, not absolute."""
#     if not offers:
#         return []


#     def column(key, default):
#         return [float(get_field(o, key, default)) for o in offers]

#     prices = column("price_eur", 0)
#     # print(prices)
#     durations = column("duration_minutes", 0)
#     environments = column("environmental_score", 50)
#     stops_list = column("stops", 0)


#     transfers_list = column("transfers", 0)
#     ratings = column("customer_rating", 4.0)
#     # print(ratings)

#     min_price, max_price = min(prices), max(prices)
#     min_dur, max_dur = min(durations), max(durations)
#     min_env, max_env = min(environments), max(environments)
#     min_stops, max_stops = min(stops_list), max(stops_list)
#     min_transfers, max_transfers = min(transfers_list), max(transfers_list)
#     min_rating, max_rating = min(ratings), max(ratings)

#     selected_preferences = resolve_preferences(trip_request)

#     preferred_departure = getattr(trip_request, "prefered_departure", "Morning")
#     start_date = getattr(trip_request, "travel_start_date", "")
#     required_luggage = getattr(trip_request, "max_luggage", "1 bags")
#     preferred_company = getattr(trip_request, "preferred_company", "None")

#     scored_offers = []

#     for o in offers:
#         # 1. normalised score (0-100) for every available attribute
#         scores = {
#             "price_eur": normalize(float(get_field(o, "price_eur", 0)), min_price, max_price, lower_better=True),
#             "duration_minutes": normalize(float(get_field(o, "duration_minutes", 0)), min_dur, max_dur, lower_better=True),
#             "environmental_score": normalize(float(get_field(o, "environmental_score", 50)), min_env, max_env, lower_better=False),
#             "stops": normalize(float(get_field(o, "stops", 0)), min_stops, max_stops, lower_better=True),
#             "transfers": normalize(float(get_field(o, "transfers", 0)), min_transfers, max_transfers, lower_better=True),
#             "customer_rating": normalize(float(get_field(o, "customer_rating", 4.0)), min_rating, max_rating, lower_better=False),

#             "departure_time": evaluate_departure_time(preferred_departure, get_field(o, "departure_time", "08:00")),
#             "travel_date": 100.0 if start_date == get_field(o, "travel_date", "") else 60.0,

#             "changeable": 100.0 if get_field(o, "changeable", False) else 0.0,
#             "refundable": 100.0 if get_field(o, "refundable", False) else 0.0,

#             "luggage_allowance": evaluate_luggage(get_field(o, "luggage_allowance", "1 bags"), required_luggage),
#             "company": evaluate_company(get_field(o, "company", ""), preferred_company),
#         }


#         # print("scored_offers -> ")
#         # print(scored_offers)

#         # 2. equal-weight total over the selected preferences only
#         valid_prefs = [p for p in selected_preferences if p in scores]

#         if valid_prefs:
#             total_score = sum(scores[p] for p in valid_prefs) / len(valid_prefs)
#         else:
#             total_score = 50.0







#         # 3. attach results to the offer
#         if isinstance(o, dict):
#             o["criterion_scores"] = scores
#             o["total_score"] = round(total_score, 1)
#         else:
#             o.criterion_scores = scores
#             o.total_score = round(total_score, 1)

#         scored_offers.append(o)

#     # 4. highest score first; ties broken by cheaper price, then shorter duration
#     scored_offers.sort(
#         key=lambda x: (
#             -float(get_field(x, "total_score", 0)),
#             float(get_field(x, "price_eur", 0)),
#             float(get_field(x, "duration_minutes", 0)),
#         )
#     )
#     return scored_offers


import copy

from helper_functions import get_field, normalize
from exceptions import ScoringError
from cust_logging import get_logger

log = get_logger()

FIXED_WEIGHTS = {
    1: [1.00],
    2: [0.70, 0.30],
    3: [0.40, 0.30, 0.30],
    4: [0.35, 0.25, 0.20, 0.20],
}
FIRST_WEIGHT = 0.30
SECOND_WEIGHT = 0.20


DEFAULT_PREFERENCES = [
    "price_eur", "duration_minutes", "departure_time",
    "environmental_score", "stops",
]

# Profile/filter names -> score keys used in the scores dict
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

# (lower_is_better, minimum meaningful spread in the criterion's own unit)
MIN_MAX_CRITERIA = {
    "price_eur": (True, 5.0),             # EUR
    "duration_minutes": (True, 60.0),     # minutes
    "stops": (True, 2.0),
    "transfers": (True, 1.0),
    "environmental_score": (False, 10.0),
    "customer_rating": (False, 0.5),
}
OTHER_CRITERIA = [
    "departure_time", "travel_date", "changeable", "refundable",
    "luggage_allowance", "company",
]
ALL_CRITERIA = list(MIN_MAX_CRITERIA) + OTHER_CRITERIA

MISSING_SCORE = 50.0            # neutral: neither rewarded nor punished
CLIP_LOW, CLIP_HIGH = 5, 95     # percentiles used to cap extreme values
MIN_OFFERS_FOR_CLIPPING = 20    # with fewer offers, percentiles are meaningless
MAX_SINGLE_WEIGHT = 0.6         # with 3+ criteria, none may carry more than 60% of the score
WEIGHT_TOLERANCE = 1e-6

TIME_WINDOWS = {
    "Morning": ("05:00", "11:59"),
    "AfterNoon": ("12:00", "16:59"),
    "Evening": ("17:00", "19:59"),
    "Night": ("20:00", "04:59"),
}
WINDOW_ORDER = ["Morning", "AfterNoon", "Evening", "Night"]


# def positional_weights(keys):
#     """Weights from the order of the traveller's preferences.

#     1 preference  -> 100%
#     2 preferences -> 50% / 50%
#     3+            -> 1st = 30%, 2nd = 20%, the remaining 50% shared equally by the rest
#     """
#     n = len(keys)
#     if n == 1:
#         return {keys[0]: 1.0}
#     if n == 2:
#         return {keys[0]: 0.5, keys[1]: 0.5}

#     rest = (1.0 - FIRST_WEIGHT - SECOND_WEIGHT) / (n - 2)
#     weights = {keys[0]: FIRST_WEIGHT, keys[1]: SECOND_WEIGHT}
#     weights.update({k: rest for k in keys[2:]})
#     return weights


def positional_weights(keys):
    """Weights from the order of the traveller's preferences (never increasing).

    1 -> 100 | 2 -> 50/50 | 3 -> 40/30/30 | 4 -> 35/25/20/20
    5+ -> 30/20 for the first two, the remaining 50% shared equally by the rest
    """
    n = len(keys)
    if n in FIXED_WEIGHTS:
        return dict(zip(keys, FIXED_WEIGHTS[n]))

    rest = (1.0 - FIRST_WEIGHT - SECOND_WEIGHT) / (n - 2)
    weights = {keys[0]: FIRST_WEIGHT, keys[1]: SECOND_WEIGHT}
    weights.update({k: rest for k in keys[2:]})
    return weights



def resolve_preferences(trip_request):
    """Score keys that count in the total (the traveller's selected preferences)."""
    traveller = getattr(trip_request, "traveller", trip_request)
    prefs = list(getattr(traveller, "mandatory_preferences", []) or [])
    prefs = [PREFERENCE_ALIASES.get(p, p) for p in prefs]
    prefs = list(dict.fromkeys(prefs))                     # remove duplicates, keep order
    return prefs or list(DEFAULT_PREFERENCES)


def validate_weights(weights, keys):
    """Returns {criterion: weight} with weights that total exactly 1.0.

    - weights=None  -> equal weights.
    - Accepts weights that total 1.0 or 100 (percent). Anything else is rejected,
      never silently re-scaled.
    """
    if weights is None:
        return {k: 1.0 / len(keys) for k in keys}

    unknown = [k for k in weights if k not in keys]
    if unknown:
        raise ScoringError(f"Weights given for criteria that are not selected: {unknown}")
    absent = [k for k in keys if k not in weights]
    if absent:
        raise ScoringError(f"Missing weights for selected criteria: {absent}")
    if any(w < 0 for w in weights.values()):
        raise ScoringError("Weights cannot be negative.")

    total = sum(weights.values())
    if abs(total - 1.0) <= WEIGHT_TOLERANCE:
        result = dict(weights)
    elif abs(total - 100.0) <= WEIGHT_TOLERANCE * 100:
        result = {k: w / 100.0 for k, w in weights.items()}
    else:
        raise ScoringError(f"Weights must total 1.0 or 100%, but they total {total:g}.")

    if len(result) > 2 and max(result.values()) > MAX_SINGLE_WEIGHT + WEIGHT_TOLERANCE:
        raise ScoringError(
            f"No single criterion may carry more than {MAX_SINGLE_WEIGHT:.0%} of the score."
        )
    return result


def _num(offer, key):
    """Number from the offer, or None when missing or not numeric."""
    value = get_field(offer, key)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if value != value else value               # NaN counts as missing


def _percentile(sorted_values, pct):
    k = (len(sorted_values) - 1) * pct / 100.0
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (k - lower)


def _build_ranges(offers):
    """(low, high) used for min-max scaling of each numeric criterion."""
    ranges = {}
    for key, (lower_is_better, floor) in MIN_MAX_CRITERIA.items():
        values = sorted(v for v in (_num(o, key) for o in offers) if v is not None)
        if not values:
            ranges[key] = None
            continue
        if len(values) >= MIN_OFFERS_FOR_CLIPPING:         # cap extreme values
            low, high = _percentile(values, CLIP_LOW), _percentile(values, CLIP_HIGH)
        else:
            low, high = values[0], values[-1]
        # a spread smaller than the minimum meaningful one is not stretched to 0-100;
        # the range grows away from the BEST end so the best offer still scores 100
        if lower_is_better:
            high = max(high, low + floor)
        else:
            low = min(low, high - floor)
        ranges[key] = (low, high)
    return ranges


# ---------------------------------------------------------- single criteria

def get_time_window(time_str: str) -> str:
    for name, (start, end) in TIME_WINDOWS.items():
        in_window = (start <= time_str <= end) if start <= end else (time_str >= start or time_str <= end)
        if in_window:
            return name
    return "Morning"


def evaluate_departure_time(preferred_departure: str, offer_time: str) -> float:
    """100 inside the preferred window, 50 one window away, 0 two windows away.
    Windows form a circle, so Night is next to Morning."""
    if preferred_departure not in WINDOW_ORDER:
        return 100.0
    offer_window = get_time_window(str(offer_time))
    diff = abs(WINDOW_ORDER.index(offer_window) - WINDOW_ORDER.index(preferred_departure))
    diff = min(diff, len(WINDOW_ORDER) - diff)
    return 100.0 - diff * 50.0


def _bag_count(text, default=1) -> int:
    try:
        return int(str(text).strip().split()[0])
    except (ValueError, IndexError):
        return default


def evaluate_luggage(offer_luggage, required_luggage) -> float:
    if not required_luggage:
        return 100.0
    return 100.0 if _bag_count(offer_luggage) >= _bag_count(required_luggage) else 0.0


def evaluate_company(offer_company, preferred_company) -> float:
    if not preferred_company or preferred_company == "None":
        return 100.0
    return 100.0 if offer_company == preferred_company else 0.0


# ------------------------------------------------------------------ ranking

def rank_offers(offers, trip_request, weights=None):
    """Scores and ranks the offers. `weights` is optional, e.g. {"price_eur": 0.4, ...}."""
    if not offers:
        return []

    # work on copies: the offers may be shared (cached), and scores must not leak between searches
    offers = [dict(o) if isinstance(o, dict) else copy.copy(o) for o in offers]

    selected = [p for p in resolve_preferences(trip_request) if p in ALL_CRITERIA]
    if not selected:
        log.warning("No recognised ranking criteria in the profile, using the defaults.")
        selected = list(DEFAULT_PREFERENCES)
    # weights = validate_weights(weights, selected)
    # update to rank
    if weights is None:
        weights = positional_weights(selected)
    weights = validate_weights(weights, selected)   

    ranges = _build_ranges(offers)
    preferred_departure = getattr(trip_request, "prefered_departure", "Morning")
    start_date = getattr(trip_request, "travel_start_date", "")
    required_luggage = getattr(trip_request, "max_luggage", "")
    preferred_company = getattr(trip_request, "preferred_company", "None")

    for o in offers:
        raw = {}                                            # score or None (= missing)

        for key, (lower_is_better, _) in MIN_MAX_CRITERIA.items():
            value = _num(o, key)
            raw[key] = None if value is None or ranges[key] is None else normalize(
                value, ranges[key][0], ranges[key][1], lower_better=lower_is_better)

        dep = get_field(o, "departure_time")
        raw["departure_time"] = evaluate_departure_time(preferred_departure, dep) if dep else None

        travel_date = get_field(o, "travel_date")
        raw["travel_date"] = None if not travel_date else (100.0 if travel_date == start_date else 50.0)

        raw["changeable"] = None if get_field(o, "changeable") is None else (
            100.0 if get_field(o, "changeable") else 0.0)

        if get_field(o, "refundable") is None:
            raw["refundable"] = None
        elif not get_field(o, "refundable"):
            raw["refundable"] = 0.0
        else:                                               # graded: a 90% refund beats a 50% refund
            pct = _num(o, "refund_advance_pct")
            raw["refundable"] = 100.0 if pct is None else max(0.0, min(100.0, pct))

        lug = get_field(o, "luggage_allowance")
        raw["luggage_allowance"] = evaluate_luggage(lug, required_luggage) if lug else None

        comp = get_field(o, "company")
        raw["company"] = evaluate_company(comp, preferred_company) if comp else None

        missing = [k for k, v in raw.items() if v is None]
        scores = {k: (MISSING_SCORE if v is None else v) for k, v in raw.items()}

        counted_missing = [k for k in missing if k in weights]
        if counted_missing:
            log.warning("Offer %s has missing values for %s (neutral score used)",
                        get_field(o, "offer_id"), counted_missing)

        contributions = {k: scores[k] * w for k, w in weights.items()}
        total = sum(contributions.values())

        # attach results (offers may be dicts or objects)
        values = {
            "criterion_scores": scores,
            "total_score": round(total, 1),
            "missing_criteria": counted_missing,
            "weights_used": weights,
            "contributions": contributions,
        }
        if isinstance(o, dict):
            o.update(values)
        else:
            for name, val in values.items():
                setattr(o, name, val)

    # highest score first; ties -> cheaper, then shorter, then offer id (always the same order)
    return sorted(
        offers,
        key=lambda x: (
            -float(get_field(x, "total_score", 0)),
            _num(x, "price_eur") if _num(x, "price_eur") is not None else float("inf"),
            _num(x, "duration_minutes") if _num(x, "duration_minutes") is not None else float("inf"),
            str(get_field(x, "offer_id", "")),
        ),
    )