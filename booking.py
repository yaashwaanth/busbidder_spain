from models import Booking
import csv
import os

BOOKINGS_FILE = "bookings.csv"

fieldnames = ["booking_id", "offer_id", "traveller_id"]


def _next_booking_number():
    """Derive the next counter from the CSV so it persists across reruns."""
    if not os.path.exists(BOOKINGS_FILE):
        return 101
    with open(BOOKINGS_FILE, newline="", encoding="utf-8") as f:
        return 101 + sum(1 for _ in csv.DictReader(f))


def book_offer(offer, traveller):
    print("Booking ->")
    print(vars(offer))
    print(vars(traveller))
    offer_id = offer["offer_id"] if isinstance(offer, dict) else offer.offer_id
    booking_id = f"{str(offer_id).upper()}-{traveller.id}-{_next_booking_number()}"


    # print("offerrrrrrrr ->" )
    # print(type(offer))


    # print(offer.available_seats)

    # dcreasing the number of seats available in a offer
    offer.available_seats -=1
    print(offer.available_seats)
    
    new_booking = Booking(booking_id, offer, traveller)
    # data = new_booking.getDetails()  
    data = {
        "booking_id": booking_id,
        "offer_id": offer_id,
        "traveller_id": traveller.id,
    }

    file_exists = os.path.exists(BOOKINGS_FILE)
    with open(BOOKINGS_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    return booking_id


def get_bookings_for(traveller_id):
    if not os.path.exists(BOOKINGS_FILE):
        return []
    with open(BOOKINGS_FILE, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row["traveller_id"] == traveller_id]