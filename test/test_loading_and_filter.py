"""Offer loading/validation (helper_functions), data.py loaders and filter.py."""
import csv

import pytest

from conftest import make_offer, make_request
from exceptions import DataFileError
from filter import filter_offers
from helper_functions import _policy, calculate_env_score, get_field, load_vaild_offers
from types import SimpleNamespace

COLUMNS = ["offer_id", "company", "destination", "travel_date", "departure_time", "arrival_time",
           "duration_minutes", "price_eur", "transfers", "stops", "luggage_allowance", "changeable",
           "refundable", "available_seats", "customer_rating", "environmental_score",
           "refund_advance_pct", "refund_same_day_pct"]


def good_row(**o):
    row = dict(offer_id="SO-101", company="SolRuta", destination="Cordoba", travel_date="2026-11-25",
               departure_time="08:00", arrival_time="12:00", duration_minutes="240", price_eur="30.5",
               transfers="1", stops="2", luggage_allowance="2 bags", changeable="True", refundable="True",
               available_seats="5", customer_rating="4.5", environmental_score="60",
               refund_advance_pct="90", refund_same_day_pct="20")
    row.update(o)
    return row


@pytest.fixture
def write_offers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)               # rejected_offers.csv is written to the cwd

    def _write(rows, columns=COLUMNS):
        path = tmp_path / "offers.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", restval="")
            w.writeheader()
            w.writerows(rows)
        return str(path)
    return _write


# loader
class TestOfferLoader:
    def test_valid_row_is_loaded_with_correct_types(self, write_offers):
        (o,) = load_vaild_offers(write_offers([good_row()]))
        assert o.price_eur == 30.5 and o.transfers == 1 and o.changeable is True
        assert o.available_seats == 5

    @pytest.mark.parametrize("field,value", [
        ("price_eur", "-5"), ("price_eur", "0"), ("price_eur", "abc"), ("price_eur", ""),
        ("duration_minutes", "-240"), ("duration_minutes", "0"),
        ("company", ""), ("destination", ""), ("travel_date", ""),
        ("travel_date", "2026-02-30"), ("travel_date", "25/11/2026"),
        ("departure_time", "8:00"), ("departure_time", "24:00"), ("departure_time", "08:60"),
        ("offer_id", "S-1"), ("offer_id", "SO101"),
        ("customer_rating", "5.1"), ("customer_rating", "-0.1"),
        ("environmental_score", "101"), ("environmental_score", "-1"),
        ("transfers", "-1"), ("stops", "-1"), ("transfers", "1.5"),
        ("available_seats", "-1"), ("luggage_allowance", "0 bags"), ("luggage_allowance", "lots"),
        ("changeable", "maybe"), ("refundable", ""),
        ("arrival_time", "13:00"),                       # does not equal departure + duration
    ])
   
   
   
   
   
   
    def test_invalid_rows_are_rejected_but_good_rows_survive(self, write_offers, field, value):
        bad = good_row(**{field: value})
        if field != "offer_id":
            bad["offer_id"] = "SO-102"
        valid = load_vaild_offers(write_offers([good_row(offer_id="SO-101"), bad]))
        assert [o.offer_id for o in valid] == ["SO-101"]

    def test_rejection_reason_is_saved_for_review(self, write_offers, tmp_path):
        load_vaild_offers(write_offers([good_row(), good_row(offer_id="SO-102", price_eur="-3")]))
        rejected = list(csv.DictReader(open(tmp_path / "rejected_offers.csv", encoding="utf-8")))
        assert len(rejected) == 1
        assert rejected[0]["source_row"] == "3" and "price" in rejected[0]["reason"]





    @pytest.mark.parametrize("field,value", [
        ("customer_rating", "0"), ("customer_rating", "5"), ("environmental_score", "0"),
        ("environmental_score", "100"), ("price_eur", "0.01"), ("transfers", "0"), ("stops", "0"),
    ])
    def test_boundary_values_are_accepted(self, write_offers, field, value):
        assert len(load_vaild_offers(write_offers([good_row(**{field: value})]))) == 1

    def test_overnight_arrival_is_valid(self, write_offers):
        row = good_row(departure_time="22:00", duration_minutes="180", arrival_time="01:00")
        assert len(load_vaild_offers(write_offers([row]))) == 1

    def test_luggage_formatting_is_corrected_not_rejected(self, write_offers):
        (o,) = load_vaild_offers(write_offers([good_row(luggage_allowance="  2   Bags ")]))
        assert o.luggage_allowance == "2 bags"




    def test_offer_id_is_uppercased(self, write_offers):
        (o,) = load_vaild_offers(write_offers([good_row(offer_id="so-101")]))
        assert o.offer_id == "SO-101"




    def test_sold_out_offer_is_kept_for_the_filter_to_hide(self, write_offers):
        (o,) = load_vaild_offers(write_offers([good_row(available_seats="0")]))
        assert o.available_seats == 0

    def test_unknown_company_and_destination_rejected_when_lists_given(self, write_offers):
        path = write_offers([good_row(offer_id="SO-101"),
                             good_row(offer_id="SO-102", company="GhostBus"),
                             good_row(offer_id="SO-103", destination="Atlantis")])
        valid = load_vaild_offers(path, known_companies={"SolRuta"}, known_destinations={"Cordoba"})
        assert [o.offer_id for o in valid] == ["SO-101"]

    def test_missing_column_rejects_the_rows(self, write_offers):
        cols = [c for c in COLUMNS if c != "price_eur"]
        path = write_offers([good_row(), good_row(offer_id="SO-102")], columns=cols)
        with pytest.raises(DataFileError):
            load_vaild_offers(path)

    def test_missing_file(self, tmp_path):
        with pytest.raises(DataFileError, match="not found"):
            load_vaild_offers(str(tmp_path / "nope.csv"))

    def test_file_with_only_invalid_rows(self, write_offers):
        with pytest.raises(DataFileError, match="No valid offers"):
            load_vaild_offers(write_offers([good_row(price_eur="-1")]))

    def test_empty_file_with_header_only(self, write_offers):
        with pytest.raises(DataFileError):
            load_vaild_offers(write_offers([]))


#  helpers
class TestHelpers:
    def test_get_field_for_dict_and_object(self):
        assert get_field({"a": 1}, "a") == 1
        assert get_field({"a": 1}, "b", "x") == "x"
        assert get_field(SimpleNamespace(a=1), "a") == 1
        assert get_field(SimpleNamespace(a=1), "b") is None

    @pytest.mark.parametrize("raw,expected", [("(90,20)", (90.0, 20.0)), ("[50|0]", (50.0, 0.0)), (" ( 100 , 100 ) ", (100.0, 100.0))])
    def test_policy_valid(self, raw, expected):
        errors = []
        assert _policy({"p": raw}, "p", errors) == expected and not errors

    @pytest.mark.parametrize("raw", ["", "abc", "(90)", "(a,b)", "(1,2,3)"])
    def test_policy_invalid_is_reported(self, raw):
        errors = []
        assert _policy({"p": raw}, "p", errors) is None
        assert errors

    @pytest.mark.xfail(reason="_policy no longer range-checks: (150,300) or same-day > advance is accepted "
                              "(the validation code is unreachable after the early return).", strict=True)
    def test_policy_rejects_out_of_range_and_inconsistent_values(self):
        errors = []
        assert _policy({"p": "(20,90)"}, "p", errors) is None
        assert errors

    def _company(self, co2, new_fleet=False):
        return SimpleNamespace(name="X", co2_g_per_km=co2, new_fleet=new_fleet)

    @pytest.mark.parametrize("co2,expected", [(55, 0), (20, 100), (10, 100), (80, 0), (37.5, 50)])
    def test_environment_score_boundaries(self, co2, expected):
        assert calculate_env_score(self._company(co2), SimpleNamespace(distance_km=100)) == expected

    def test_environment_score_bonus_is_capped_at_100(self):
        assert calculate_env_score(self._company(20, True), SimpleNamespace(distance_km=100)) == 100

    def test_environment_score_works_with_the_real_BusCompany_model(self):
        from models import BusCompany
        bc = BusCompany(name="A", bus_code="AAA", price_per_km=.05, co2_g_per_km=30, direct_route=True,
                        departure_window=("06:00", "10:00"), coastal_focus=False, budget_company=False,
                        bus_avg_speed=60, cancellation_policy=(90, 20), new_fleet=False)
        assert 0 <= calculate_env_score(bc, SimpleNamespace(distance_km=100)) <= 100


# data.py
class TestDataLoaders:
    DEST_HEADER = "key,name,costal,major_city,distance_km,base_duration_min,base_price_eur\n"

    def test_destinations_valid_and_invalid_rows(self, tmp_path):
        from data import load_destinations
        p = tmp_path / "d.csv"
        p.write_text(self.DEST_HEADER + "Toledo,Toledo,false,false,70,60,6\n"
                     "Bad,Bad,true,true,notanumber,60,6\n", encoding="utf-8")
        d = load_destinations(str(p))
        assert list(d) == ["Toledo"] and d["Toledo"].distance_km == 70.0

    @pytest.mark.xfail(reason="BUG: a row with too few columns gives None -> to_bool(None) raises "
                              "AttributeError, which the loader does not catch, so one short row "
                              "crashes the whole load.", strict=True)
    def test_destinations_short_row_is_skipped_not_fatal(self, tmp_path):
        from data import load_destinations
        p = tmp_path / "d.csv"
        p.write_text(self.DEST_HEADER + "Toledo,Toledo,false,false,70,60,6\nShort,Short,true\n", encoding="utf-8")
        assert list(load_destinations(str(p))) == ["Toledo"]

    def test_destinations_missing_or_empty(self, tmp_path):
        from data import load_destinations
        with pytest.raises(DataFileError):
            load_destinations(str(tmp_path / "missing.csv"))
        p = tmp_path / "d.csv"
        p.write_text("key,name,costal,major_city,distance_km,base_duration_min,base_price_eur\n", encoding="utf-8")
        with pytest.raises(DataFileError):
            load_destinations(str(p))

    BUS_HEADER = ("name,bus_code,price_per_km,co2_g_per_km,departure_start,departure_end,direct_route,"
                  "coastal_focus,new_fleet,budget_company,bus_avg_speed,cancellation_policy\n")

    def test_bus_company_valid_row(self, tmp_path):
        from data import load_bus_companies
        p = tmp_path / "b.csv"
        p.write_text(self.BUS_HEADER + 'SolRuta,SOL,0.05,32,06:00,14:00,false,false,false,true,50,"(90,20)"\n',
                     encoding="utf-8")
        c = load_bus_companies(str(p))
        assert c["SolRuta"].cancellation_policy == (90.0, 20.0)

    def test_bus_company_bad_rows_are_skipped(self, tmp_path):
        from data import load_bus_companies
        p = tmp_path / "b.csv"
        p.write_text(self.BUS_HEADER +
                     'Good,GOO,0.05,32,06:00,14:00,false,false,false,true,50,"(90,20)"\n'
                     'BadCode,TOOLONG,0.05,32,06:00,14:00,false,false,false,true,50,"(90,20)"\n'
                     'BadPolicy,BAD,0.05,32,06:00,14:00,false,false,false,true,50,oops\n'
                     'BadNum,BNM,abc,32,06:00,14:00,false,false,false,true,50,"(90,20)"\n', encoding="utf-8")
        assert list(load_bus_companies(str(p))) == ["Good"]


# filter
class TestFilter:
    def run(self, offer=None, **req):
        return filter_offers([offer or make_offer()], make_request(**req))

    def test_matching_offer_passes(self):
        assert len(self.run()) == 1

    def test_destination_is_case_insensitive(self):
        assert self.run(destination="cordoba")

    def test_wrong_destination_rejected(self):
        assert not self.run(destination="Bilbao")

    @pytest.mark.parametrize("date,passes", [
        ("2026-11-21", False), ("2026-11-22", True), ("2026-11-30", True), ("2026-12-01", False)])
    def test_date_window_is_inclusive(self, date, passes):
        assert bool(self.run(make_offer(travel_date=date))) is passes

    @pytest.mark.parametrize("price,passes", [(99.99, True), (100.0, True), (100.01, False)])
    def test_budget_boundary(self, price, passes):
        assert bool(self.run(make_offer(price_eur=price))) is passes

    @pytest.mark.parametrize("transfers,passes", [(2, True), (3, True), (4, False)])
    def test_transfers_boundary(self, transfers, passes):
        assert bool(self.run(make_offer(transfers=transfers))) is passes

    @pytest.mark.parametrize("stops,passes", [(4, True), (5, True), (6, False)])
    def test_stops_boundary(self, stops, passes):
        assert bool(self.run(make_offer(stops=stops), max_stops=5)) is passes

    @pytest.mark.parametrize("minutes,passes", [(299, True), (300, True), (301, False)])
    def test_duration_boundary(self, minutes, passes):
        assert bool(self.run(make_offer(duration_minutes=minutes), max_duration=5)) is passes

    @pytest.mark.parametrize("seats,passes", [(0, False), (1, True)])
    def test_seat_boundary(self, seats, passes):
        assert bool(self.run(make_offer(available_seats=seats))) is passes

    @pytest.mark.parametrize("lug,passes", [("1 bags", False), ("2 bags", True), ("3 bags", True)])
    def test_luggage_boundary(self, lug, passes):
        assert bool(self.run(make_offer(luggage_allowance=lug), max_luggage="2 bags")) is passes

    def test_flexibility_requirement(self):
        assert not self.run(make_offer(changeable=False), flexiblity=True)
        assert self.run(make_offer(changeable=False), flexiblity=False)

    def test_preferred_company(self):
        assert self.run(make_offer(company="SolRuta"), preferred_company="SolRuta")
        assert not self.run(make_offer(company="CostaLink"), preferred_company="SolRuta")
        assert self.run(make_offer(company="CostaLink"), preferred_company="None")

    def test_empty_input_and_no_matches(self):
        assert filter_offers([], make_request()) == []
        assert filter_offers([make_offer(price_eur=500)], make_request()) == []

    def test_filter_keeps_only_passing_offers_in_order(self):
        offers = [make_offer(offer_id="SO-101"), make_offer(offer_id="SO-102", price_eur=500),
                  make_offer(offer_id="SO-103")]
        assert [o.offer_id for o in filter_offers(offers, make_request())] == ["SO-101", "SO-103"]
