from models import Offer

def filter_offers(offers,trip_request):
    """Filters the offers before ranking them based on the mandatory requirements of the traveller"""
    filtered = []

    for offer in offers:
        if offer.destination.lower() != trip_request.destination.lower():
            continue
        if not(trip_request.travel_start_date<= offer.travel_date <= trip_request.travel_end_date ):
            continue
        if offer.price_eur>trip_request.budget:
            continue
        if offer.transfers > trip_request.max_transfers:
            continue
        if offer.available_seats < 1:
            continue
        if offer.luggage_allowance.split()[0] < trip_request.max_luggage.split()[0]:
            continue
        if offer.duration_minutes/60 > trip_request.max_duration:
            continue
        if offer.changeable and not trip_request.flexiblity:
            continue
        if trip_request.preferred_company != "None" and trip_request.preferred_company != offer.company:
            continue
        if offer.stops > trip_request.max_stops:
            continue
        filtered.append(offer)

    return filtered








