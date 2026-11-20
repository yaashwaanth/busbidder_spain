# BusBidder Spain

A modular Python application that **filters and ranks competing bus offers** for an individual traveller.
Five simulated bus companies return offers; the program first removes offers that break the traveller's
mandatory constraints, then ranks the rest with a transparent weighted scoring model and explains
**why** the top offer ranks first and which trade-offs remain.

---

## Features

- Traveller profiles (saved in `travelers.csv`) with their own ranking preferences
- Automatically generated offers for the next 90 days (reproducible, `random.seed(42)`), including
  deliberately bad records to exercise data validation
- **Filtering** by destination, dates, budget, duration, transfers, stops, luggage, flexibility and company
- **Weighted ranking** on a 0-100 scale with a plain-language explanation for every offer
- Booking, cancellation with refund rules (before travel date / on travel date), and simulated card payment
- Logging to `busbidder.log`; invalid offers are written to `rejected_offers.csv` with the reason

## Requirements

- Python 3.10 or newer
- Packages in `requirements.txt` (Streamlit for the interface, pytest for the tests)

## Installation

```bash
pip install -r requirements.txt
```

## Running the application

```bash
streamlit run app.py
```

1. Choose or register a traveller in the sidebar and pick their ranking preferences (in order of importance).
2. Select destination, preferred departure time and the mandatory filters.
3. Open **Search Offers** and press **Search** to see ranked offers and the **Why this rank?** explanation.
4. Book an offer (card details are only format-checked; no real payment happens).
5. Use **My Bookings** to view or cancel bookings and see the refund.

## Running the tests

```bash
pytest -v                # all tests
pytest --cov=rank --cov=filter --cov=booking --cov=payment --cov=helper_functions --cov=data
```

## How it works

```
offers.py  ->  filter.py  ->  rank.py  ->  explaination_of_offer.py  ->  app.py (UI)
(generate &    (mandatory     (score &      (why this rank?)
 validate)      constraints)   sort)                    booking.py / payment.py
```

### Scoring model

```
Score(offer) = sum( weight_k x score_k(offer) )        score_k in [0, 100], weights total 1.0
```

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit user interface |
| `main.py` | Simple console demo (may need updating to the current models) |
| `models.py` | `Traveller`, `Destination`, `BusCompany`, `Offer`, `Trip_Request`, `Booking` |
| `offers.py` | Generates simulated offers |
| `filter.py` | Removes offers that violate mandatory constraints |
| `rank.py` | Normalisation, weights, scoring and sorting |
| `explaination_of_offer.py` | Data-based explanations of ranks |
| `booking.py` | Bookings, cancellations, refunds, seat counts |
| `payment.py` | Card format validation and masked payment logging |
| `helper_functions.py` | Offer loader/validator, traveller storage, helpers |
| `data.py`, `constants.py` | Load bus companies and destinations from CSV |
| `regex_patters.py` | Validation patterns |
| `exceptions.py`, `cust_logging.py` | Custom exceptions and logging |
| `tests/` | pytest suite |

## Limitations

- Offers are simulated; payment is not real and card numbers are only format-checked.
- Scores are relative to the offers that matched the filters, so they are not an objective "best".
- With fewer than 20 offers, outlier clipping is switched off because percentiles are unreliable.