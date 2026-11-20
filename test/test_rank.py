"""Scoring model: normalisation, weights, ties, missing values, extreme values."""
import math

import pytest

from conftest import make_offer, make_offer_dict, make_request
from exceptions import ScoringError
from helper_functions import normalize
from rank import (
    DEFAULT_PREFERENCES, MISSING_SCORE, evaluate_company, evaluate_departure_time,
    evaluate_luggage, get_time_window, positional_weights, rank_offers,
    resolve_preferences, validate_weights,
)


# ------------------------------------------------------------ normalisation
class TestNormalize:
    def test_lower_is_better(self):
        assert normalize(10, 10, 20, lower_better=True) == 100.0
        assert normalize(20, 10, 20, lower_better=True) == 0.0
        assert normalize(15, 10, 20, lower_better=True) == 50.0

    def test_higher_is_better(self):
        assert normalize(10, 10, 20, lower_better=False) == 0.0
        assert normalize(20, 10, 20, lower_better=False) == 100.0
        assert normalize(12.5, 10, 20, lower_better=False) == 25.0

    @pytest.mark.parametrize("value,lower,expected", [
        (5, True, 100.0), (25, True, 0.0), (5, False, 0.0), (25, False, 100.0),
    ])
    def test_values_outside_range_are_clamped(self, value, lower, expected):
        assert normalize(value, 10, 20, lower_better=lower) == expected

    def test_all_equal_values_do_not_divide_by_zero(self):
        assert normalize(7, 7, 7) == 100.0


# ------------------------------------------------------------------ weights
class TestPositionalWeights:
    @pytest.mark.parametrize("n", range(1, 9))
    def test_always_total_one_and_never_increase(self, n):
        w = list(positional_weights([f"k{i}" for i in range(n)]).values())
        assert math.isclose(sum(w), 1.0)
        assert w == sorted(w, reverse=True)

    def test_fixed_tables(self):
        assert list(positional_weights(["a", "b"]).values()) == [0.70, 0.30]
        assert list(positional_weights(list("abcd")).values()) == [0.35, 0.25, 0.20, 0.20]

    def test_five_or_more_share_the_remainder_equally(self):
        w = positional_weights(list("abcde"))
        assert w["a"] == 0.30 and w["b"] == 0.20
        assert math.isclose(w["c"], 0.5 / 3)


class TestValidateWeights:
    KEYS = ["price_eur", "duration_minutes", "departure_time"]

    def test_none_gives_equal_weights(self):
        w = validate_weights(None, self.KEYS)
        assert all(math.isclose(v, 1 / 3) for v in w.values())

    def test_fractions_totalling_one_are_accepted(self):
        w = validate_weights({"price_eur": .4, "duration_minutes": .3, "departure_time": .3}, self.KEYS)
        assert math.isclose(sum(w.values()), 1.0)

    def test_percentages_totalling_100_are_converted(self):
        w = validate_weights({"price_eur": 40, "duration_minutes": 30, "departure_time": 30}, self.KEYS)
        assert w["price_eur"] == pytest.approx(0.4)

    @pytest.mark.parametrize("bad", [
        {"price_eur": .4, "duration_minutes": .3, "departure_time": .2},      # 0.9
        {"price_eur": .5, "duration_minutes": .4, "departure_time": .3},      # 1.2
        {"price_eur": 50, "duration_minutes": 30, "departure_time": 30},      # 110
    ])
    def test_wrong_totals_are_rejected_not_rescaled(self, bad):
        with pytest.raises(ScoringError, match="total"):
            validate_weights(bad, self.KEYS)

    def test_negative_weight_rejected(self):
        with pytest.raises(ScoringError, match="negative"):
            validate_weights({"price_eur": -.1, "duration_minutes": .6, "departure_time": .5}, self.KEYS)

    def test_weight_for_unselected_criterion_rejected(self):
        with pytest.raises(ScoringError, match="not selected"):
            validate_weights({"price_eur": .5, "duration_minutes": .3, "departure_time": .1, "stops": .1}, self.KEYS)

    def test_missing_weight_for_selected_criterion_rejected(self):
        with pytest.raises(ScoringError, match="Missing"):
            validate_weights({"price_eur": .5, "duration_minutes": .5}, self.KEYS)

    def test_dominance_cap_boundary(self):
        ok = {"price_eur": .6, "duration_minutes": .2, "departure_time": .2}
        assert validate_weights(ok, self.KEYS)["price_eur"] == pytest.approx(.6)     # exactly 60% is allowed
        over = {"price_eur": .61, "duration_minutes": .2, "departure_time": .19}
        with pytest.raises(ScoringError, match="more than 60%"):
            validate_weights(over, self.KEYS)

    def test_cap_does_not_apply_to_one_or_two_criteria(self):
        assert validate_weights({"price_eur": 1.0}, ["price_eur"]) == {"price_eur": 1.0}
        assert validate_weights({"price_eur": .9, "stops": .1}, ["price_eur", "stops"])["price_eur"] == .9

    def test_tiny_float_error_is_tolerated(self):
        w = {"price_eur": .1 + .2, "duration_minutes": .3, "departure_time": .4}   # 1.0000000000000002 style
        assert validate_weights(w, self.KEYS)


class TestResolvePreferences:
    def test_aliases_and_duplicates(self):
        req = make_request(["max_luggage", "luggage", "budget", "price_eur"])
        assert resolve_preferences(req) == ["luggage_allowance", "price_eur"]

    def test_empty_preferences_fall_back_to_defaults(self):
        assert resolve_preferences(make_request([])) == DEFAULT_PREFERENCES


# --------------------------------------------------- single-criterion scores
class TestTimeWindows:
    @pytest.mark.parametrize("t,window", [
        ("05:00", "Morning"), ("11:59", "Morning"), ("12:00", "AfterNoon"),
        ("16:59", "AfterNoon"), ("17:00", "Evening"), ("19:59", "Evening"),
        ("20:00", "Night"), ("23:59", "Night"), ("00:00", "Night"), ("04:59", "Night"),
    ])
    def test_window_boundaries(self, t, window):
        assert get_time_window(t) == window

    def test_circular_distance(self):
        assert evaluate_departure_time("Morning", "08:00") == 100.0
        assert evaluate_departure_time("Morning", "13:00") == 50.0    # one window away
        assert evaluate_departure_time("Morning", "18:00") == 0.0     # two windows away
        assert evaluate_departure_time("Morning", "22:00") == 50.0    # Night is next to Morning

    def test_unknown_preference_does_not_penalise(self):
        assert evaluate_departure_time("None", "03:00") == 100.0

    @pytest.mark.xfail(reason="Known gap: 'Afternoon' (normal spelling) is not 'AfterNoon', "
                              "so it is silently treated as 'no preference'.", strict=True)
    def test_normal_spelling_of_afternoon_is_recognised(self):
        assert evaluate_departure_time("Afternoon", "03:00") < 100.0


def test_luggage_and_company_scores():
    assert evaluate_luggage("3 bags", "2 bags") == 100.0
    assert evaluate_luggage("2 bags", "2 bags") == 100.0      # boundary: equal is enough
    assert evaluate_luggage("1 bags", "2 bags") == 0.0
    assert evaluate_luggage("2 bags", "") == 100.0
    assert evaluate_luggage("garbage", "1 bag") == 100.0      # unreadable falls back to 1 bag
    assert evaluate_company("SolRuta", "None") == 100.0
    assert evaluate_company("SolRuta", "SolRuta") == 100.0
    assert evaluate_company("CostaLink", "SolRuta") == 0.0


# ------------------------------------------------------------------ ranking
def ids(ranked):
    return [o.offer_id if hasattr(o, "offer_id") else o["offer_id"] for o in ranked]


class TestRankingNormal:
    def test_empty_input_returns_empty_list(self):
        assert rank_offers([], make_request()) == []

    def test_cheaper_offer_wins_on_price(self):
        offers = [make_offer(offer_id="SO-101", price_eur=40), make_offer(offer_id="SO-102", price_eur=20)]
        assert ids(rank_offers(offers, make_request(["price_eur"]))) == ["SO-102", "SO-101"]

    def test_higher_rating_and_env_score_win(self):
        offers = [make_offer(offer_id="SO-101", environmental_score=20),
                  make_offer(offer_id="SO-102", environmental_score=90)]
        assert ids(rank_offers(offers, make_request(["environmental_score"])))[0] == "SO-102"

    def test_total_is_bounded_and_equals_sum_of_contributions(self):
        offers = [make_offer(offer_id=f"SO-{100+i}", price_eur=20 + i * 7, duration_minutes=200 + i * 90,
                             environmental_score=30 + i * 10) for i in range(6)]
        req = make_request(["price_eur", "duration_minutes", "environmental_score", "departure_time"])
        for o in rank_offers(offers, req):
            assert 0 <= o.total_score <= 100
            assert o.total_score == pytest.approx(sum(o.contributions.values()), abs=0.051)
            assert sum(o.weights_used.values()) == pytest.approx(1.0)
            assert all(0 <= s <= 100 for s in o.criterion_scores.values())

    def test_result_is_sorted_by_total_score_descending(self):
        offers = [make_offer(offer_id=f"SO-{100+i}", price_eur=20 + i * 9) for i in range(5)]
        totals = [o.total_score for o in rank_offers(offers, make_request(["price_eur"]))]
        assert totals == sorted(totals, reverse=True)

    def test_inputs_are_not_mutated(self):
        offers = [make_offer(offer_id="SO-101"), make_offer(offer_id="SO-102", price_eur=50)]
        as_dicts = [make_offer_dict(offer_id="SO-103")]
        rank_offers(offers, make_request())
        rank_offers(as_dicts, make_request())
        assert not hasattr(offers[0], "total_score")
        assert "total_score" not in as_dicts[0]

    def test_works_for_dicts_and_objects(self):
        d = rank_offers([make_offer_dict(offer_id="SO-101")], make_request())
        o = rank_offers([make_offer(offer_id="SO-101")], make_request())
        assert d[0]["total_score"] == o[0].total_score

    def test_custom_weights_change_the_order(self):
        cheap_slow = make_offer(offer_id="SO-101", price_eur=20, duration_minutes=600)
        dear_fast = make_offer(offer_id="SO-102", price_eur=60, duration_minutes=180)
        req = make_request(["price_eur", "duration_minutes"])
        by_price = rank_offers([cheap_slow, dear_fast], req, {"price_eur": .9, "duration_minutes": .1})
        by_time = rank_offers([cheap_slow, dear_fast], req, {"price_eur": .1, "duration_minutes": .9})
        assert ids(by_price)[0] == "SO-101"
        assert ids(by_time)[0] == "SO-102"

    def test_invalid_weights_raise_from_rank_offers(self):
        with pytest.raises(ScoringError):
            rank_offers([make_offer()], make_request(["price_eur", "stops"]), {"price_eur": .5, "stops": .2})

    def test_unrecognised_preferences_fall_back_to_defaults(self):
        ranked = rank_offers([make_offer()], make_request(["colour_of_bus"]))
        assert set(ranked[0].weights_used) == set(DEFAULT_PREFERENCES)

    def test_refundable_score_is_graded_by_refund_percentage(self):
        big = make_offer(offer_id="SO-101", refund_advance_pct=90)
        small = make_offer(offer_id="SO-102", refund_advance_pct=50)
        ranked = rank_offers([small, big], make_request(["refundable"]))
        assert ids(ranked) == ["SO-101", "SO-102"]
        assert ranked[0].criterion_scores["refundable"] == 90.0

    def test_non_refundable_scores_zero(self):
        r = rank_offers([make_offer(refundable=False, refund_advance_pct=0)], make_request(["refundable"]))
        assert r[0].criterion_scores["refundable"] == 0.0


class TestRankingBoundary:
    def test_single_offer_gets_full_marks_on_min_max_criteria(self):
        r = rank_offers([make_offer()], make_request(["price_eur", "duration_minutes"]))
        assert r[0].total_score == 100.0

    def test_small_spreads_are_not_stretched_to_0_100(self):
        # 1 EUR difference is below the 5 EUR minimum spread: 11 EUR must not score 0
        offers = [make_offer(offer_id="SO-101", price_eur=10.0), make_offer(offer_id="SO-102", price_eur=11.0)]
        r = {o.offer_id: o for o in rank_offers(offers, make_request(["price_eur"]))}
        assert r["SO-101"].criterion_scores["price_eur"] == 100.0
        assert r["SO-102"].criterion_scores["price_eur"] == pytest.approx(80.0)

    def test_spread_exactly_at_the_floor_is_fully_stretched(self):
        offers = [make_offer(offer_id="SO-101", price_eur=10.0), make_offer(offer_id="SO-102", price_eur=15.0)]
        r = {o.offer_id: o for o in rank_offers(offers, make_request(["price_eur"]))}
        assert r["SO-102"].criterion_scores["price_eur"] == 0.0

    @pytest.mark.parametrize("n_normal,clipped", [(18, False), (39, True)])
    def test_extreme_price_only_clipped_with_enough_offers(self, n_normal, clipped):
        """19 offers: no clipping (outlier squashes everyone to ~100). 40 offers: clipped."""
        offers = [make_offer(offer_id=f"SO-{1000+i}", price_eur=20 + i) for i in range(n_normal)]
        offers.append(make_offer(offer_id="SO-9999", price_eur=10_000))
        by_id = {o.offer_id: o for o in rank_offers(offers, make_request(["price_eur"]))}
        mid = by_id["SO-1010"].criterion_scores["price_eur"]       # price 30
        if clipped:
            assert 60 < mid < 95
            assert by_id["SO-9999"].criterion_scores["price_eur"] == 0.0
        else:
            assert mid > 99                                        # outlier dominated the scale

    def test_one_criterion_cannot_dominate_through_weights(self):
        keys = ["price_eur", "duration_minutes", "stops"]
        with pytest.raises(ScoringError):
            rank_offers([make_offer()], make_request(keys), {"price_eur": .9, "duration_minutes": .05, "stops": .05})


class TestTieBreaking:
    def test_equal_scores_cheaper_first(self):
        offers = [make_offer(offer_id="SO-101", price_eur=40), make_offer(offer_id="SO-102", price_eur=30)]
        ranked = rank_offers(offers, make_request(["departure_time"]))   # same score for both
        assert ranked[0].total_score == ranked[1].total_score
        assert ids(ranked) == ["SO-102", "SO-101"]

    def test_then_shorter_duration(self):
        offers = [make_offer(offer_id="SO-101", duration_minutes=300), make_offer(offer_id="SO-102", duration_minutes=200)]
        assert ids(rank_offers(offers, make_request(["departure_time"]))) == ["SO-102", "SO-101"]

    def test_then_offer_id_so_order_is_deterministic(self):
        a, b = make_offer(offer_id="SO-102"), make_offer(offer_id="SO-101")
        assert ids(rank_offers([a, b], make_request(["departure_time"]))) == ["SO-101", "SO-102"]
        assert ids(rank_offers([b, a], make_request(["departure_time"]))) == ["SO-101", "SO-102"]


class TestMissingAndInvalidValues:
    @pytest.mark.parametrize("bad", [None, "", "abc", float("nan")])
    def test_unusable_price_gets_neutral_score_and_is_flagged(self, bad):
        good = make_offer(offer_id="SO-101", price_eur=20)
        broken = make_offer(offer_id="SO-102", price_eur=bad)
        r = {o.offer_id: o for o in rank_offers([good, broken], make_request(["price_eur"]))}
        assert r["SO-102"].criterion_scores["price_eur"] == MISSING_SCORE
        assert r["SO-102"].missing_criteria == ["price_eur"]
        assert r["SO-101"].missing_criteria == []

    def test_missing_value_for_uncounted_criterion_is_not_flagged(self):
        o = rank_offers([make_offer(customer_rating=None)], make_request(["price_eur"]))[0]
        assert o.missing_criteria == []

    def test_missing_departure_time_and_company(self):
        o = rank_offers([make_offer(departure_time="", company="")],
                        make_request(["departure_time", "company"]))[0]
        assert set(o.missing_criteria) == {"departure_time", "company"}
        assert o.total_score == 50.0

    def test_dict_with_key_absent_entirely(self):
        d = make_offer_dict()
        del d["price_eur"]
        r = rank_offers([d, make_offer_dict(offer_id="SO-102")], make_request(["price_eur"]))
        assert any("price_eur" in x["missing_criteria"] for x in r)

    def test_all_values_missing_for_a_criterion_does_not_crash(self):
        offers = [make_offer(offer_id="SO-101", price_eur=None), make_offer(offer_id="SO-102", price_eur=None)]
        r = rank_offers(offers, make_request(["price_eur"]))
        assert [o.total_score for o in r] == [50.0, 50.0]

    def test_missing_flag_fields_get_neutral_score(self):
        o = rank_offers([make_offer(changeable=None)], make_request(["changeable"]))[0]
        assert o.criterion_scores["changeable"] == MISSING_SCORE

    def test_missing_value_does_not_beat_a_real_good_value(self):
        good = make_offer(offer_id="SO-101", price_eur=20)
        broken = make_offer(offer_id="SO-102", price_eur=None)
        worse = make_offer(offer_id="SO-103", price_eur=80)
        ranked = rank_offers([broken, worse, good], make_request(["price_eur"]))
        assert ids(ranked)[0] == "SO-101"
        assert ids(ranked)[-1] == "SO-103" or ids(ranked)[-1] == "SO-102"
