from statistics import median

LABELS = {
    "price_eur": "price", "duration_minutes": "duration",
    "departure_time": "departure time", "environmental_score": "environmental score",
    "stops": "stops", "transfers": "transfers", "customer_rating": "customer rating",
    "changeable": "changeable fare", "refundable": "refundable fare",
    "luggage_allowance": "luggage", "company": "company",
}

def _median(offers, key, scale=1.0):
    values = [v for v in (_number(o, key) for o in offers) if v is not None]
    return median(values) / scale if values else None


def _get(o, key):
    return o[key] if isinstance(o, dict) else getattr(o, key)

def _top_contributions(offer, n=2):
    contributions = _get(offer, "contributions")
    best = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return ", ".join(f"{LABELS.get(k, k)} ({v:.1f} points)" for k, v in best)


def _number(o, key):
    """Float value of a field, or None when it is missing or not numeric."""
    try:
        value = float(_get(o, key))
    except (KeyError, AttributeError, TypeError, ValueError):
        return None
    return None if value != value else value



def _get_or(o, key, default=None):
    try:
        return _get(o, key)
    except (KeyError, AttributeError):
        return default


def ranking_criteria(trip_request):
    """Score keys that actually count in the total (the traveller's selected preferences)."""
    traveller = getattr(trip_request, "traveller", None)
    prefs = list(getattr(traveller, "mandatory_preferences", []) or [])
    prefs = ["luggage_allowance" if p == "max_luggage" else p for p in prefs]
    if not prefs:
        prefs = ["price_eur", "duration_minutes", "departure_time",
                 "environmental_score", "stops"]
    return prefs


def _weights_text(offer, used=None):
    w = _get(offer, "weights_used")
    keys = used if used is not None else w
    return ", ".join(f"{LABELS.get(k, k)} {w[k]*100:.0f}%" for k in keys if k in w)


def e(ranked, trip_request, tolerance=0.05):
    """Short explanation of why ranked[0] is first, generated from the data."""




    top, n = ranked[0], len(ranked)
    criteria = ranking_criteria(trip_request)
    scores = _get(top, "criterion_scores")

    pros, cons = [], []

    # compare with the other matching offers (only meaningful if n > 1)
    if n > 1:
        med_price = median(float(_get(o, "price_eur")) for o in ranked)
        med_dur = median(float(_get(o, "duration_minutes")) for o in ranked) / 60
        med_rating = median(float(_get(o, "customer_rating")) for o in ranked)
        med_env = median(float(_get(o, "environmental_score")) for o in ranked)
        med_transfers = median(float(_get(o, "transfers")) for o in ranked)

        price = float(_get(top, "price_eur"))
        if price < med_price * (1 - tolerance):
            pros.append(f"a lower price ({price:.2f} € vs a median of {med_price:.2f} €)")
        elif price > med_price * (1 + tolerance):
            cons.append(f"a higher price ({price:.2f} € vs a median of {med_price:.2f} €)")

        dur = float(_get(top, "duration_minutes")) / 60
        if dur < med_dur * (1 - tolerance):
            pros.append(f"a shorter journey ({dur:.1f} h vs a median of {med_dur:.1f} h)")
        elif dur > med_dur * (1 + tolerance):
            cons.append(f"a longer journey ({dur:.1f} h vs a median of {med_dur:.1f} h)")

        rating = float(_get(top, "customer_rating"))
        if rating > med_rating + 0.2:
            pros.append(f"a higher customer rating ({rating:.1f} vs a median of {med_rating:.1f})")
        elif rating < med_rating - 0.2:
            cons.append(f"a lower customer rating ({rating:.1f} vs a median of {med_rating:.1f})")

        env = float(_get(top, "environmental_score"))
        if env > med_env + 5:
            pros.append(f"a better environmental score ({env:.0f} vs a median of {med_env:.0f})")
        elif env < med_env - 5:
            cons.append(f"a worse environmental score ({env:.0f} vs a median of {med_env:.0f})")

        if int(_get(top, "transfers")) > med_transfers:
            cons.append(f"more transfers than most matching offers ({_get(top, 'transfers')})")

    # facts that do not depend on comparison
    transfers, stops = int(_get(top, "transfers")), int(_get(top, "stops"))
    if transfers == 0 and stops == 0:
        pros.append("a direct route with no transfers or intermediate stops")
    elif transfers == 0:
        pros.append("no transfers")

    window = getattr(trip_request, "prefered_departure", "")
    dep_time = _get(top, "departure_time")
    if scores.get("departure_time") == 100.0:
        pros.append(f"a departure at {dep_time}, inside your preferred {window} window")
        # print(pros)
    else:
        cons.append(f"a departure at {dep_time}, outside your preferred {window} window")

    changeable, refundable = _get(top, "changeable"), _get(top, "refundable")
    if changeable and refundable:
        pros.append("a flexible fare (changeable and refundable)")


        
    elif changeable:
        pros.append("a changeable fare")
    elif refundable:
        pros.append("a refundable fare")



    else:
        cons.append("a fare that is neither changeable nor refundable")

    # strongest / weakest among the criteria that count
    used = {k: scores[k] for k in criteria if k in scores}
    best = max(used, key=used.get) if used else None
    worst = min(used, key=used.get) if used else None

    # assemble
    text = [f"**Why it ranks #1:** it has the highest total score "
            f"({_get(top, 'total_score')}/100) among {n} offer(s) that passed your filters, "

            # f"using equal weights on: {', '.join(LABELS.get(k, k) for k in used)}."]

            f"using these weights: {_weights_text(top, used)}."]

    if n > 1:
        gap = float(_get(top, "total_score")) - float(_get(ranked[1], "total_score"))
        sentence = f"It leads the #2 offer by {gap:.1f} points."
        if gap < 2:
            sentence += " The margin is small, so different weights could change the order."
        text.append(sentence)
    else:
        text.append("It is the only offer that matched, so there is nothing to compare it with.")

    if pros:
        text.append("**Advantages:** " + "; ".join(pros) + ".")
    if cons:
        text.append("**Trade-offs:** " + "; ".join(cons) + ".")
   
   
    else:
        text.append("**Trade-offs:** none notable compared with the other matching offers.")

    if best and worst and best != worst:
        text.append(f"Its strongest criterion is {LABELS.get(best, best)} "
                    f"({used[best]:.0f}/100) and its weakest is {LABELS.get(worst, worst)} "
                    f"({used[worst]:.0f}/100).")

    text.append("_This is the top result only under your selected constraints, weights and "
                "scoring assumptions (scores are relative to the offers that matched). "
                "It is not an objective best._")
    return "\n\n".join(text)



def explain_offer(offer, rank, ranked, trip_request):
    """Short data-based explanation of why one offer sits at its rank."""
    n = len(ranked)
    criteria = ranking_criteria(trip_request)
    scores = _get(offer, "criterion_scores")
    used = {k: scores[k] for k in criteria if k in scores}
    total = float(_get(offer, "total_score"))

    lines = [f"**Rank #{rank} of {n}** with a total score of {total}/100 "
            #  f"(equal weights on: {', '.join(LABELS.get(k, k) for k in used)})."
             

             f"(weights: {_weights_text(offer, used)})."
             
             ]

    # gap to the leader
    if rank > 1:
        top = ranked[0]
        gap = float(_get(top, "total_score")) - total
        lines.append(f"It scores {gap:.1f} points below the #1 offer.")

    # strengths and weaknesses among the criteria that count
    strong = [LABELS.get(k, k) for k, v in used.items() if v >= 80]
    weak = [LABELS.get(k, k) for k, v in used.items() if v <= 40]






    if strong:
        lines.append("**Strong on:** " + ", ".join(strong) + ".")

    if weak:
        lines.append("**Weak on:** " + ", ".join(weak) + ".")


    if not strong and not weak:
        lines.append("Its scores are mid-range on all counted criteria.")

    # comparison with the other matching offers
    if n > 1:
        med_price = median(float(_get(o, "price_eur")) for o in ranked)
        med_dur = median(float(_get(o, "duration_minutes")) for o in ranked) / 60
        price = float(_get(offer, "price_eur"))
        dur = float(_get(offer, "duration_minutes")) / 60
        facts = []
        facts.append(f"price {price:.2f} € ({'below' if price < med_price else 'above' if price > med_price else 'at'} the {med_price:.2f} € median)")
        facts.append(f"duration {dur:.1f} h ({'shorter than' if dur < med_dur else 'longer than' if dur > med_dur else 'equal to'} the {med_dur:.1f} h median)")
        lines.append("**Compared with matching offers:** " + "; ".join(facts) + ".")

    if rank > 1 and weak:
        lines.append(f"Its weaker scores on {', '.join(weak)} help explain why it ranks below #1.")

    lines.append("_Valid only under your selected constraints and scoring assumptions._")
    return "\n\n".join(lines)

def _missing_note(offer):
    missing = _get_or(offer, "missing_criteria", []) or []
    if not missing:
        return None
    names = ", ".join(LABELS.get(k, k) for k in missing)
    return f"Data was missing for {names}; a neutral score of 50 was used for it."



def explain_top_offer(ranked, trip_request, tolerance=0.05):
    """Short explanation of why ranked[0] is first, generated from the data."""
    top, n = ranked[0], len(ranked)
    criteria = ranking_criteria(trip_request)
    scores = _get(top, "criterion_scores")

    pros, cons = [], []

    # --- compare with the other matching offers (only meaningful if n > 1) ---
    if n > 1:
        med_price = _median(ranked, "price_eur")
        med_dur = _median(ranked, "duration_minutes", 60)
        med_rating = _median(ranked, "customer_rating")
        med_env = _median(ranked, "environmental_score")
        med_transfers = _median(ranked, "transfers")

        price = _number(top, "price_eur")
        if price is not None and med_price is not None:
            if price < med_price * (1 - tolerance):
                pros.append(f"a lower price ({price:.2f} € vs a median of {med_price:.2f} €)")
            elif price > med_price * (1 + tolerance):
                cons.append(f"a higher price ({price:.2f} € vs a median of {med_price:.2f} €)")

        dur = _number(top, "duration_minutes")
        dur = dur / 60 if dur is not None else None
        if dur is not None and med_dur is not None:
            if dur < med_dur * (1 - tolerance):
                pros.append(f"a shorter journey ({dur:.1f} h vs a median of {med_dur:.1f} h)")
            elif dur > med_dur * (1 + tolerance):
                cons.append(f"a longer journey ({dur:.1f} h vs a median of {med_dur:.1f} h)")

        rating = _number(top, "customer_rating")
        if rating is not None and med_rating is not None:
            if rating > med_rating + 0.2:
                pros.append(f"a higher customer rating ({rating:.1f} vs a median of {med_rating:.1f})")
            elif rating < med_rating - 0.2:
                cons.append(f"a lower customer rating ({rating:.1f} vs a median of {med_rating:.1f})")

        env = _number(top, "environmental_score")
        if env is not None and med_env is not None:
            if env > med_env + 5:
                pros.append(f"a better environmental score ({env:.0f} vs a median of {med_env:.0f})")
            elif env < med_env - 5:
                cons.append(f"a worse environmental score ({env:.0f} vs a median of {med_env:.0f})")

        top_transfers = _number(top, "transfers")
        if top_transfers is not None and med_transfers is not None and top_transfers > med_transfers:
            cons.append(f"more transfers than most matching offers ({int(top_transfers)})")

    # --- facts that do not depend on comparison ---
    transfers, stops = _number(top, "transfers"), _number(top, "stops")
    if transfers == 0 and stops == 0:
        pros.append("a direct route with no transfers or intermediate stops")
    elif transfers == 0:
        pros.append("no transfers")

    window = getattr(trip_request, "prefered_departure", "")
    dep_time = _get(top, "departure_time")
    if scores.get("departure_time") == 100.0:
        pros.append(f"a departure at {dep_time}, inside your preferred {window} window")
    else:
        cons.append(f"a departure at {dep_time}, outside your preferred {window} window "
                    f"(convenience score {scores.get('departure_time', 0):.0f}/100)")

    changeable, refundable = _get(top, "changeable"), _get(top, "refundable")
    refund_pct = float(_get_or(top, "refund_advance_pct", 0) or 0)
    if changeable and refundable:
        pros.append(f"a flexible fare (changeable, and {refund_pct:g}% refundable before the travel date)")
    elif changeable:
        pros.append("a changeable fare")
    elif refundable:
        pros.append(f"a refundable fare ({refund_pct:g}% before the travel date)")
    else:
        cons.append("a fare that is neither changeable nor refundable")

    # --- strongest / weakest among the criteria that count ---
    used = {k: scores[k] for k in criteria if k in scores}
    best = max(used, key=used.get) if used else None
    worst = min(used, key=used.get) if used else None

    # --- assemble ---
    text = [f"**Why it ranks #1:** it has the highest total score "
            f"({_get(top, 'total_score')}/100) among {n} offer(s) that passed your filters, "
            f"using these weights: {_weights_text(top)}."]

    if n > 1:
        gap = float(_get(top, "total_score")) - float(_get(ranked[1], "total_score"))
        sentence = f"It leads the #2 offer by {gap:.1f} points."
        if gap < 2:
            sentence += " The margin is small, so different weights could change the order."
        text.append(sentence)
    else:
        text.append("It is the only offer that matched, so there is nothing to compare it with.")

    text.append(f"Its biggest contributions to the score are {_top_contributions(top)}.")

    if pros:
        text.append("**Advantages:** " + "; ".join(pros) + ".")
    if cons:
        text.append("**Trade-offs:** " + "; ".join(cons) + ".")
    else:
        text.append("**Trade-offs:** none notable compared with the other matching offers.")

    if best and worst and best != worst:
        text.append(f"Its strongest criterion is {LABELS.get(best, best)} "
                    f"({used[best]:.0f}/100) and its weakest is {LABELS.get(worst, worst)} "
                    f"({used[worst]:.0f}/100).")

    note = _missing_note(top)
    if note:
        text.append(note)

    text.append("_This is the top result only under your selected constraints, weights and "
                "scoring assumptions (scores are relative to the offers that matched). "
                "It is not an objective best._")
    return "\n\n".join(text)
