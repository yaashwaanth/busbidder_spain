import csv
import os
from datetime import datetime, date

from models import Booking
from helper_functions import get_field
from collections import Counter


from exceptions import BookingError, InvalidReferenceError, CancellationError
from cust_logging import get_logger
from regex_patters import OFFER_ID_RE, BOOKING_REF_RE

log = get_logger()


BOOKINGS_FILE = "bookings.csv"

fieldnames = [
    "booking_id", "offer_id", "traveller_id", "booked_at",
    "company", "travel_date", "departure_time",
    "price_paid_eur", "luggage_allowance",
    "changeable", "refundable",
    "refund_advance_pct", "refund_same_day_pct",
    "status", "cancelled_at", "refund_eur",
]


def _read_all():
    """Reads every booking. Older files without the new columns are treated as ACTIVE."""
    if not os.path.exists(BOOKINGS_FILE):
        return []
    with open(BOOKINGS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["status"] = r.get("status") or "ACTIVE"
        r["cancelled_at"] = r.get("cancelled_at") or ""
        r["refund_eur"] = r.get("refund_eur") or ""
    return rows


def _write_all(rows):
    with open(BOOKINGS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)


def _next_booking_number():
    """Counts all bookings, cancelled ones included, so booking ids stay unique."""
    return 101 + len(_read_all())


def build_fare_conditions(offer):
    """Snapshot of the fare as it was when the traveller booked."""
    return {
        "company": get_field(offer, "company"),
        "travel_date": get_field(offer, "travel_date"),
        "departure_time": get_field(offer, "departure_time"),
        "price_paid_eur": f"{float(get_field(offer, 'price_eur', 0)):.2f}",
        "luggage_allowance": get_field(offer, "luggage_allowance"),
        "changeable": bool(get_field(offer, "changeable", False)),
        "refundable": bool(get_field(offer, "refundable", False)),
        "refund_advance_pct": get_field(offer, "refund_advance_pct", 0),
        "refund_same_day_pct": get_field(offer, "refund_same_day_pct", 0),
    }


def book_offer(offer, traveller):
    offer_id = get_field(offer, "offer_id")

    if not OFFER_ID_RE.match(str(offer_id)):
        raise BookingError(f"Invalid offer id: {offer_id}")
    booking_id = f"{str(offer_id).upper()}-{traveller.id}-{_next_booking_number()}"

    if not BOOKING_REF_RE.match(booking_id):
        raise InvalidReferenceError(f"Booking reference has invlaid format: {booking_id}")
    

    fare = build_fare_conditions(offer)
    new_booking = Booking(booking_id, traveller, offer, fare_conditions=fare)

    data = {
        "booking_id": booking_id,
        "offer_id": offer_id,
        "traveller_id": traveller.id,
        "booked_at": datetime.now().isoformat(timespec="seconds"),
        **fare,
        "status": "ACTIVE",
        "cancelled_at": "",
        "refund_eur": "",
    }

    # reducing the seats
    

    rows = _read_all()
    rows.append(data)
    _write_all(rows)   # upgrades an old bookings.csv to the new columns

    log.info("Booking created: %s | traveller=%s | paid=%s EUR", booking_id, traveller.id, fare["price_paid_eur"])
    return booking_id


def get_bookings_for(traveller_id):
    return [r for r in _read_all() if r["traveller_id"] == traveller_id]


def refund_amounts(row):
    """Returns (refund if cancelled before travel date, refund if cancelled on travel date) in EUR."""
    if str(row["refundable"]) != "True":
        return 0.0, 0.0
    price = float(row["price_paid_eur"])
    before = round(price * float(row["refund_advance_pct"]) / 100, 2)
    on_day = round(price * float(row["refund_same_day_pct"]) / 100, 2)
    return before, on_day


def refund_if_cancelled_today(row):
    """Refund in EUR if the booking is cancelled today."""
    travel_date = datetime.strptime(row["travel_date"], "%Y-%m-%d").date()
    today = date.today()
    before, on_day = refund_amounts(row)
    if today < travel_date:
        return before
    if today == travel_date:
        return on_day
    return 0.0


def can_cancel(row):
    """Active bookings can be cancelled up to and including the travel date."""
    travel_date = datetime.strptime(row["travel_date"], "%Y-%m-%d").date()
    return row["status"] == "ACTIVE" and date.today() <= travel_date


def cancel_booking(booking_id, traveller_id):
    """Marks the booking as cancelled and returns the refund in EUR."""

    if not BOOKING_REF_RE.match(str(booking_id)):
        raise InvalidReferenceError(f"Invalid booking reference: {booking_id!r}")
    
    rows = _read_all()
    for r in rows:
        if r["booking_id"] == booking_id and r["traveller_id"] == traveller_id:
            if r["status"] == "CANCELLED":
                raise CancellationError("This booking is already cancelled.")
            if not can_cancel(r):
                raise ValueError("The travel date has passed, so this booking can no longer be cancelled.")
            refund = refund_if_cancelled_today(r)
            r["status"] = "CANCELLED"
            r["cancelled_at"] = datetime.now().isoformat(timespec="seconds")
            r["refund_eur"] = f"{refund:.2f}"
            _write_all(rows)
            log.info("Booking cancelled: %s | refund=%.2f EUR", booking_id, refund)
            return refund
        
    raise CancellationError("Booking not found.")






def seats_booked():
    """Counts ACTIVE bookings per (offer_id, travel_date)."""
    return Counter(
        (r["offer_id"], r["travel_date"])
        for r in _read_all()
        if r["status"] == "ACTIVE"
    )