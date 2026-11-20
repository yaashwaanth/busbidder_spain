"""Explanations must be generated from data and stay robust when data is missing."""
import pytest

from conftest import make_offer, make_request
from explaination_of_offer import explain_offer, explain_top_offer, ranking_criteria
from rank import rank_offers

PREFS = ["price_eur", "duration_minutes", "departure_time"]


@pytest.fixture
def ranked():
    offers = [
        make_offer(offer_id="SO-101", price_eur=20, duration_minutes=200, departure_time="08:00"),
        make_offer(offer_id="SO-102", price_eur=45, duration_minutes=400, departure_time="21:00",
                   changeable=False, refundable=False, transfers=2, stops=5, refund_advance_pct=0),
        make_offer(offer_id="SO-103", price_eur=30, duration_minutes=300, departure_time="13:00"),
    ]
    return rank_offers(offers, make_request(PREFS))


def test_top_explanation_has_expected_sections(ranked):
    text = explain_top_offer(ranked, make_request(PREFS))
    assert "Why it ranks #1" in text and "3 offer(s)" in text
    assert "Advantages" in text and "Trade-offs" in text
    assert "not an objective best" in text
    assert "lower price" in text            # SO-101 is cheapest -> must be listed as an advantage


def test_top_explanation_mentions_the_actual_gap(ranked):
    gap = ranked[0].total_score - ranked[1].total_score
    assert f"{gap:.1f} points" in explain_top_offer(ranked, make_request(PREFS))


def test_single_offer_has_nothing_to_compare(ranked):
    text = explain_top_offer(ranked[:1], make_request(PREFS))
    assert "only offer" in text and "leads the #2" not in text


def test_small_margin_warning():
    twins = [make_offer(offer_id="SO-101", price_eur=20), make_offer(offer_id="SO-102", price_eur=20.05)]
    r = rank_offers(twins, make_request(["price_eur", "duration_minutes"]))
    assert "margin is small" in explain_top_offer(r, make_request(["price_eur", "duration_minutes"]))


def test_missing_data_is_reported_and_does_not_crash():
    offers = [make_offer(offer_id="SO-101", customer_rating=None, environmental_score=None, price_eur=None),
              make_offer(offer_id="SO-102", price_eur=30)]
    req = make_request(["price_eur", "duration_minutes"])
    r = rank_offers(offers, req)
    text = explain_top_offer(r, req)
    assert text
    broken = next(o for o in r if o.offer_id == "SO-101")
    assert "neutral score of 50" in explain_top_offer([broken, *[o for o in r if o is not broken]], req)


def test_explain_offer_for_lower_ranks(ranked):
    text = explain_offer(ranked[-1], len(ranked), ranked, make_request(PREFS))
    assert f"Rank #{len(ranked)} of {len(ranked)}" in text
    assert "below the #1 offer" in text


def test_explain_offer_for_rank_one_has_no_gap_sentence(ranked):
    assert "below the #1" not in explain_offer(ranked[0], 1, ranked, make_request(PREFS))


def test_ranking_criteria_matches_the_ranker_for_unaliased_names():
    assert ranking_criteria(make_request(PREFS)) == PREFS
    assert ranking_criteria(make_request([])) == ["price_eur", "duration_minutes", "departure_time",
                                                  "environmental_score", "stops"]


@pytest.mark.xfail(reason="INCONSISTENCY: explanation's ranking_criteria only maps 'max_luggage', while "
                          "rank.resolve_preferences maps many aliases (budget, preferred_company, ...), so the "
                          "'strongest/weakest criterion' text can use different criteria than the score.",
                   strict=True)
def test_explanation_uses_the_same_criteria_as_the_ranker():
    from rank import resolve_preferences
    req = make_request(["budget", "preferred_company", "max_luggage"])
    assert ranking_criteria(req) == resolve_preferences(req)
