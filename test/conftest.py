import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Offer, Traveller, Trip_Request  # noqa: E402


def make_offer(**overrides):
    """A valid Offer object; override any field to build a specific case."""
    base = dict(
        offer_id="SO-101", company="SolRuta", destination="Cordoba",
        travel_date="2026-11-25", departure_time="08:00", duration_minutes=240.0,
        arrival_time="12:00", price_eur=30.0, transfers=0, luggage_allowance="2 bags",
        changeable=True, refundable=True, available_seats=10, customer_rating=4.2,
        environmental_score=60, stops=0, refund_advance_pct=90.0, refund_same_day_pct=20.0,
    )
    base.update(overrides)
    return Offer(**base)


def make_offer_dict(**overrides):
    return dict(vars(make_offer(**overrides)))


def make_traveller(prefs=None, tid="Raol-101"):
    return Traveller(id=tid, name="Raol", age=24, gender="M", phone="94324303",
                     email="raol@gmail.com", traveller_type="Business",
                     mandatory_preferences=prefs if prefs is not None else ["price_eur"])


def make_request(prefs=None, **overrides):
    base = dict(
        traveller=make_traveller(prefs), destination="Cordoba", max_stops=15,
        travel_start_date="2026-11-22", travel_end_date="2026-11-30", budget=100.0,
        max_transfers=3, max_luggage="1 bags", prefered_departure="Morning",
        max_duration=24.0, flexiblity=False, preferred_company="None",
    )
    base.update(overrides)
    return Trip_Request(**base)


@pytest.fixture
def offer_factory():
    return make_offer


@pytest.fixture
def request_factory():
    return make_request


@pytest.fixture
def traveller():
    return make_traveller()
