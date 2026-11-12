from models import Offer

def filter_offers(offers:Offer,trip_request):
    """Filters the offers before ranking them based on the mandatory requirements of the traveller"""
    if not offers:
        return []

    # Extract values for normalization using your exact attribute names (`price`, `duration`)
    prices = [o.price for o in offers]
    durations = [o.duration for o in offers]
    
    min_price, max_price = min(prices), max(prices)
    min_duration, max_duration = min(durations), max(durations)

    scored_offers = []

    for o in offers:
        scores = {}

        # --- 1. Price Score (Lower price = higher score) ---
        if max_price == min_price:
            scores["Price"] = 100.0
        else:
            scores["Price"] = max(0.0, min(100.0, ((max_price - o.price) / (max_price - min_price)) * 100.0))

        # --- 2. Duration Score (Shorter duration = higher score) ---
        if max_duration == min_duration:
            scores["Duration"] = 100.0
        else:
            scores["Duration"] = max(0.0, min(100.0, ((max_duration - o.duration) / (max_duration - min_duration)) * 100.0))

        # --- 3. Departure Time Score ---
        scores["DepartureTime"] = evaluate_departure_time(o.departure_time)

        # --- 4. Flexibility Score (Using your exact attributes: changeablity, refundablity) ---
        flex_score = 0.0
        if getattr(o, "changeablity", False):
            flex_score += 40.0
        if getattr(o, "refundablity", False):
            flex_score += 40.0
        if o.transfers == 0:
            flex_score += 20.0  # Direct route bonus
        scores["Flexibility"] = min(100.0, flex_score)

        # --- 5. Environmental Score (Using environmental_measure) ---
        try:
            scores["Environment"] = float(o.environmental_measure)
        except (TypeError, ValueError):
            scores["Environment"] = 50.0

        # --- 6. Weighted Final Calculation ---
        # Balanced default weights across criteria
        weights = {
            "Price": 0.35,
            "Duration": 0.25,
            "DepartureTime": 0.15,
            "Flexibility": 0.15,
            "Environment": 0.10
        }

        total_weighted_score = sum(scores[criterion] * weight for criterion, weight in weights.items())
        
        # Attach runtime metadata directly to the Offer instance
        o.criterion_scores = scores
        o.total_score = round(total_weighted_score, 1)
        
        scored_offers.append(o)

    # Sort descending so the highest scoring offer is ranked first (#1)
    scored_offers.sort(key=lambda x: x.total_score, reverse=True)
    return scored_offers




