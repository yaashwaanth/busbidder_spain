import csv
import logging
from datetime import date, timedelta

import pytest

import booking
from conftest import make_offer, make_traveller
from exceptions import BookingError, CancellationError, InvalidReferenceError, PaymentError
from payment import log_payment, validate_card
from regex_patters import (BOOKING_REF_RE, BUS_CODE_RE, CARD_RE, CVV_RE, EXPIRY_RE,
                           LUGGAGE_RE, OFFER_ID_RE, TIME_RE)


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


@pytest.fixture(autouse=True)
def bookings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(booking, "BOOKINGS_FILE", str(tmp_path / "bookings.csv"))
    return tmp_path / "bookings.csv"


# booking
class TestBooking:
    def test_booking_id_format_and_persistence(self, traveller):
        bid = booking.book_offer(make_offer(travel_date=day(5)), traveller)
        assert bid == "SO-101-Raol-101-101"
        assert BOOKING_REF_RE.match(bid)
        (row,) = booking.get_bookings_for("Raol-101")
        assert row["status"] == "ACTIVE" and row["price_paid_eur"] == "30.00"

    def test_ids_stay_unique_after_a_cancellation(self, traveller):
        o = make_offer(travel_date=day(5))
        first = booking.book_offer(o, traveller)
        booking.cancel_booking(first, "Raol-101")
        second = booking.book_offer(o, traveller)
        assert first != second and second.endswith("-102")

    def test_fare_conditions_are_a_snapshot_of_the_offer(self, traveller):
        o = make_offer(travel_date=day(5), price_eur=45.5, refund_advance_pct=70)
        booking.book_offer(o, traveller)
        o.price_eur = 999                       # later price change must not affect the booking
        assert booking.get_bookings_for("Raol-101")[0]["price_paid_eur"] == "45.50"

    @pytest.mark.parametrize("bad_id", ["", "SO101", "S-1", "so-101", None])
    def test_invalid_offer_id_raises_booking_error(self, traveller, bad_id):
        with pytest.raises(BookingError):
            booking.book_offer(make_offer(offer_id=bad_id), traveller)

    def test_traveller_id_that_breaks_the_reference_format(self):
        with pytest.raises(InvalidReferenceError):
            booking.book_offer(make_offer(), make_traveller(tid="A-101"))   # name part too short

    def test_bookings_are_private_to_each_traveller(self, traveller):
        booking.book_offer(make_offer(travel_date=day(5)), traveller)
        assert booking.get_bookings_for("Anna-102") == []

    def test_seats_booked_counts_only_active(self, traveller):
        o = make_offer(travel_date=day(5))
        a = booking.book_offer(o, traveller)
        booking.book_offer(o, traveller)
        booking.cancel_booking(a, "Raol-101")
        assert booking.seats_booked()[("SO-101", day(5))] == 1

    def test_legacy_file_without_status_columns_is_treated_as_active(self, bookings_file):
        with open(bookings_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["booking_id", "offer_id", "traveller_id", "travel_date"])
            w.writerow(["SO-101-Raol-101-101", "SO-101", "Raol-101", day(3)])
        assert booking.get_bookings_for("Raol-101")[0]["status"] == "ACTIVE"
        assert booking.seats_booked()[("SO-101", day(3))] == 1

    def test_missing_file_means_no_bookings(self):
        assert booking.get_bookings_for("Raol-101") == [] and not booking.seats_booked()

    @pytest.mark.xfail(reason="GAP: book_offer has no seat check (SoldOutError is only raised in app.py), "
                              "and has a '# reducing the seats' placeholder; the booking layer itself "
                              "allows overbooking.", strict=True)
    def test_booking_layer_refuses_sold_out_offer(self, traveller):
        from exceptions import SoldOutError
        with pytest.raises(SoldOutError):
            booking.book_offer(make_offer(available_seats=0, travel_date=day(5)), traveller)


# ------------------------------------------------------------------ refunds
class TestRefunds:
    ROW = dict(refundable="True", price_paid_eur="50.00", refund_advance_pct="90", refund_same_day_pct="20")

    def test_refund_amounts(self):
        assert booking.refund_amounts(self.ROW) == (45.0, 10.0)

    def test_non_refundable_gets_nothing(self):
        assert booking.refund_amounts({**self.ROW, "refundable": "False"}) == (0.0, 0.0)

    @pytest.mark.parametrize("pct,expected", [("0", 0.0), ("100", 50.0)])
    def test_percentage_boundaries(self, pct, expected):
        assert booking.refund_amounts({**self.ROW, "refund_advance_pct": pct})[0] == expected

    def test_refund_rounding_to_cents(self):
        row = {**self.ROW, "price_paid_eur": "33.33", "refund_advance_pct": "33"}
        assert booking.refund_amounts(row)[0] == 11.0

    @pytest.mark.parametrize("offset,expected", [(1, 45.0), (0, 10.0), (-1, 0.0)])
    def test_refund_depends_on_travel_date(self, offset, expected):
        row = {**self.ROW, "travel_date": day(offset)}
        assert booking.refund_if_cancelled_today(row) == expected

    @pytest.mark.parametrize("offset,status,ok", [
        (1, "ACTIVE", True), (0, "ACTIVE", True), (-1, "ACTIVE", False), (1, "CANCELLED", False)])
    def test_can_cancel_boundaries(self, offset, status, ok):
        assert booking.can_cancel({"travel_date": day(offset), "status": status}) is ok


class TestCancellation:
    def book(self, traveller, offset=5, **o):
        return booking.book_offer(make_offer(travel_date=day(offset), **o), traveller)

    def test_cancel_returns_refund_and_marks_row(self, traveller):
        bid = self.book(traveller, price_eur=50)
        assert booking.cancel_booking(bid, "Raol-101") == 45.0
        row = booking.get_bookings_for("Raol-101")[0]
        assert row["status"] == "CANCELLED" and row["refund_eur"] == "45.00" and row["cancelled_at"]

    def test_cancel_on_travel_day_uses_same_day_percentage(self, traveller):
        assert booking.cancel_booking(self.book(traveller, offset=0, price_eur=50), "Raol-101") == 10.0

    def test_cancel_non_refundable_refunds_zero(self, traveller):
        bid = self.book(traveller, refundable=False, refund_advance_pct=0, refund_same_day_pct=0)
        assert booking.cancel_booking(bid, "Raol-101") == 0.0

    def test_cancelling_twice_fails(self, traveller):
        bid = self.book(traveller)
        booking.cancel_booking(bid, "Raol-101")
        with pytest.raises(CancellationError, match="already"):
            booking.cancel_booking(bid, "Raol-101")

    def test_past_travel_date_cannot_be_cancelled(self, traveller):
        bid = self.book(traveller, offset=-1)
        with pytest.raises(ValueError, match="passed"):
            booking.cancel_booking(bid, "Raol-101")

    def test_unknown_booking(self, traveller):
        with pytest.raises(CancellationError, match="not found"):
            booking.cancel_booking("SO-101-Raol-101-999", "Raol-101")

    def test_other_traveller_cannot_cancel(self, traveller):
        bid = self.book(traveller)
        with pytest.raises(CancellationError, match="not found"):
            booking.cancel_booking(bid, "Anna-102")
        assert booking.get_bookings_for("Raol-101")[0]["status"] == "ACTIVE"

    @pytest.mark.parametrize("ref", ["", "garbage", "SO-101", "SO-101-Raol-101"])
    def test_malformed_reference(self, ref):
        with pytest.raises(InvalidReferenceError):
            booking.cancel_booking(ref, "Raol-101")

    @pytest.mark.xfail(reason="INCONSISTENCY: a too-late cancellation raises plain ValueError while every "
                              "other cancellation failure raises CancellationError, so a handler for "
                              "BusBidderError would miss it.", strict=True)
    def test_late_cancellation_raises_a_domain_error(self, traveller):
        bid = self.book(traveller, offset=-1)
        with pytest.raises(CancellationError):
            booking.cancel_booking(bid, "Raol-101")


# payment
class TestPayment:
    def test_valid_card_returns_digits_only(self):
        assert validate_card("4111 1111 1111 1111", "12/30", "123") == "4111111111111111"

    @pytest.mark.parametrize("number", ["", "1234", "4111 1111 1111 111", "4111 1111 1111 11111",
                                        "abcd efgh ijkl mnop", "4111-1111-1111-1111"])
    def test_invalid_card_numbers(self, number):
        with pytest.raises(PaymentError, match="16 digits"):
            validate_card(number, "12/30", "123")

    @pytest.mark.parametrize("expiry", ["", "1/30", "13/30", "00/30", "12/2030", "12-30", "ab/cd"])
    def test_invalid_expiry(self, expiry):
        with pytest.raises(PaymentError, match="MM/YY"):
            validate_card("4111111111111111", expiry, "123")

    @pytest.mark.parametrize("expiry", ["01/30", "12/30", " 12/30 "])
    def test_valid_expiry_boundaries(self, expiry):
        assert validate_card("4111111111111111", expiry, "123")

    @pytest.mark.parametrize("cvv", ["", "12", "12345", "abc", "1 2"])
    def test_invalid_cvv(self, cvv):
        with pytest.raises(PaymentError, match="CVV"):
            validate_card("4111111111111111", "12/30", cvv)

    @pytest.mark.parametrize("cvv", ["123", "1234"])
    def test_valid_cvv_lengths(self, cvv):
        assert validate_card("4111111111111111", "12/30", cvv)

    @pytest.mark.xfail(reason="GAP: validate_card only checks the format; an expired card (01/20) is accepted.",
                       strict=True)
    def test_expired_card_is_rejected(self):
        with pytest.raises(PaymentError):
            validate_card("4111111111111111", "01/20", "123")

    def test_log_masks_the_card_number(self, caplog):
        with caplog.at_level(logging.INFO, logger="busbidder"):
            log_payment("Raol-101", "SO-101", 30.0, "4111111111111234")
        text = caplog.text
        assert "****1234" in text and "4111111111111234" not in text


# -------------------------------------------------------------------- regex
@pytest.mark.parametrize("regex,good,bad", [
    (OFFER_ID_RE, ["SO-101", "CA-1234"], ["S-101", "SO-10", "so-101", "SO101", "SO-101 ", ""]),
    (TIME_RE, ["00:00", "08:30", "23:59"], ["24:00", "8:30", "12:60", "12:5", "ab:cd", ""]),
    (BUS_CODE_RE, ["SOL", "CAE"], ["SO", "SOLL", "sol", "S0L", ""]),
    (LUGGAGE_RE, ["1 bag", "2 bags", "10 bags"], ["0 bags", "bags", "2bags", "2  bags", "-1 bags", ""]),
    (CARD_RE, ["1234567890123456"], ["123456789012345", "12345678901234567", "abcdefghijklmnop"]),
    (EXPIRY_RE, ["01/26", "12/99"], ["00/26", "13/26", "1/26", "12/2026"]),
    (CVV_RE, ["123", "1234"], ["12", "12345", "12a"]),
    (BOOKING_REF_RE, ["SO-101-Raol-101-105", "CA-1234-Anna Maria-102-1001"],
     ["SO-101-R-101-105", "SO-101-Raol-10-105", "SO-101-Raol-101", "SO-101-Raol_1-101-105"]),
])
def test_regex_accepts_and_rejects(regex, good, bad):
    assert all(regex.match(g) for g in good)
    assert not any(regex.match(b) for b in bad)


@pytest.mark.xfail(reason="re.match with '$' also accepts a trailing newline ('08:30\\n'); "
                          "use re.fullmatch or \\Z.", strict=True)
@pytest.mark.parametrize("regex,value", [(TIME_RE, "08:30\n"), (OFFER_ID_RE, "SO-101\n"), (CARD_RE, "1234567890123456\n")])
def test_regex_rejects_trailing_newline(regex, value):
    assert not regex.match(value)
