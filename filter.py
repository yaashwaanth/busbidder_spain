from models import Offer

def filter_offers(offers:Offer,trip_request):
    """Filters the offers before ranking them based on the mandatory requirements of the traveller"""
    filtered = []

    for offer in offers:
        if offer.destination.lower() != trip_request.destination.lower():
            continue
        if not(trip_request.travel_date<= offer.travel_start_date <= offer.travel_end_date ):
            continue
        if offer.price> trip_request.budget:
            continue
        if offer.transfers > trip_request.max_transfers:
            continue
        if offer.available_seats < 1:
            continue
        if offer.luggage_allowance < trip_request.max_luggage:
            continue
        if offer.duration > trip_request.max_duration:
            continue
        if offer.changeablity and not trip_request.flexiblity:
            continue

        filtered.append(offer)

    return filtered




