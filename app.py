import re

import streamlit as st

from offers import create_automated_offers
from models import Traveller, Trip_Request
from filter import filter_offers
from rank import rank_offers
from helper_functions import load_travellers, save_traveller, generate_traveller_id
from constants import BUS_COMPANIES
from booking import book_offer, get_bookings_for,refund_if_cancelled_today, refund_amounts, can_cancel, cancel_booking,seats_booked
from explaination_of_offer import explain_offer, LABELS,ranking_criteria,explain_top_offer
from exceptions import BusBidderError, DataFileError, SoldOutError
from cust_logging import get_logger
from payment import validate_card, log_payment


from exceptions import DataFileError


log = get_logger()

st.set_page_config(page_title="BusBidder Spain", page_icon="🌊", layout="wide")

st.title("🌊 BusBidder Spain")
st.markdown("### Welcome ###")



@st.cache_resource
def load_offers():
    offers = create_automated_offers()
    # offers are regenerated on every server start, so re-apply existing active bookings once
    booked = seats_booked()
    for o in offers:
        o.available_seats = max(0, o.available_seats - booked.get((o.offer_id, o.travel_date), 0))
    return offers


# with st.spinner("Generating and loading bus offers..."):
#     all_offers = load_offers()
try:

    with st.spinner("Generating and loading bus offers..."):
        all_offers = load_offers()

except DataFileError as e:
    log.error("[%s] %s", e.category, e)
    st.error(f"Data problem: {e}")
    st.stop()

offers_by_id = {o.offer_id: o for o in all_offers}

# TRAVELLER PROFILE inSide Traveler profile
st.sidebar.header("👤 Traveller Profile")

saved_travellers = load_travellers()
traveller_names = list(saved_travellers.keys())

profile_mode = st.sidebar.radio(
    "Profile Action",
    ["Select Existing Traveller", "Create New Traveller"],
    key="profile_mode_radio",
)

if profile_mode == "Select Existing Traveller":
    selected_name = st.sidebar.selectbox(
        "Choose Traveller", traveller_names, key="select_existing_traveller_box"
    )
    traveller = saved_travellers[selected_name]
    st.sidebar.success(f"Loaded profile: **{traveller.name}**")

else:
    st.sidebar.subheader("Register New Traveller")

    # OUTSIDE the form, so changing it reruns the script and updates the defaults
    traveller_type = st.sidebar.selectbox(
        "Traveller Type",
        ["Business", "Student", "Flexible", "Eco-Conscious"],
        key="new_traveller_type",
    )

    available_prefs = {
        "Company": "company",
        "Price (€)": "price_eur",
        "Duration": "duration_minutes",
        "Departure Time": "departure_time",
        "Environmental Score": "environmental_score",
        "Stops": "stops",
        "Transfers": "transfers",
        "Customer Rating": "customer_rating",
        "Changeable": "changeable",
        "Refundable": "refundable",
        "Luggage": "max_luggage",
    }

    DEFAULT_PREFS = {
        "Business": ["Duration", "Stops", "Company", "Transfers"],
        "Student": ["Price (€)", "Luggage", "Refundable", "Company"],
        "Flexible": ["Refundable", "Changeable", "Departure Time", "Price (€)"],
        "Eco-Conscious": ["Environmental Score", "Company", "Departure Time", "Price (€)"],
    }
    default_pref = DEFAULT_PREFS.get(traveller_type, [])

    with st.sidebar.form("new_traveller_form"):
        name = st.text_input("Name", key="new_traveller_name")
        age = st.number_input("Age", min_value=1, max_value=120, value=25, key="new_traveller_age")
        gender = st.selectbox("Gender", ["M", "F", "Other"], key="new_traveller_gender")
        phone = st.text_input("Phone", value="943XXXXX", key="new_traveller_phone")
        email = st.text_input("Email", value="user@gmail.com", key="new_traveller_email")

        selected_pref_labels = st.multiselect(
            "Mandatory Ranking Preferences:",
            options=list(available_prefs.keys()),
            default=default_pref,
            key=f"new_traveller_prefs_{traveller_type}",  # key changes with the type
        )
        submitted = st.form_submit_button("Save Traveller")

        if submitted:
            name_pattern = r"^[A-Za-zÀ-ÿ\s]{2,40}$"
            phone_pattern = r"^\d{8,10}$"
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

            cleaned_name = name.strip()
            cleaned_phone = phone.strip()
            cleaned_email = email.strip()

            if not re.match(name_pattern, cleaned_name):
                st.error("Invalid Name: Must contain only letters and spaces (2 to 40 characters, no numbers).")
            elif not re.match(email_pattern, cleaned_email):
                st.error("Invalid Email: Please enter a valid email address (ex: user@gmail.com).")
            elif not re.match(phone_pattern, cleaned_phone):
                st.error("Invalid Phone: Please enter a valid phone number.")
            else:
                new_traveller = Traveller(
                    id=generate_traveller_id(cleaned_name),
                    name=cleaned_name, age=age, gender=gender,
                    phone=cleaned_phone, email=cleaned_email,
                    traveller_type=traveller_type,
                    mandatory_preferences=[available_prefs[p] for p in selected_pref_labels],
                )
                save_traveller(new_traveller)
                st.success(
                    f"Traveller {cleaned_name} saved successfully! "
                    "Switch to 'Select Existing Traveller' to use it."
                )

    traveller = saved_travellers[traveller_names[0]]

# SIDEBAR
trip_request = {}

destinations_list = sorted(set(o.destination for o in all_offers))

st.sidebar.subheader("🔍 Search")
trip_request["destination"] = st.sidebar.selectbox("Destination", destinations_list)
trip_request["travel_start_date"] = st.sidebar.date_input("Travel Start Date (Mandatory)", key="mand_start_date")
trip_request["travel_end_date"] = st.sidebar.date_input("Travel End Date (Mandatory)", key="mand_end_date")
trip_request["prefered_departure"] = st.sidebar.selectbox(
    "Preferred Departure Time Window (Mandatory)",
    ["Morning", "AfterNoon", "Evening", "Night"],
    key="mand_departure",
)

company_options = ["None"] + [comp.name for comp in BUS_COMPANIES.values()]

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 User Mandatory Preference Filters")
st.sidebar.caption("Criteria selected in your profile for scoring and ranking:")

mand_prefs = getattr(traveller, "mandatory_preferences", [])
if isinstance(mand_prefs, str):
    mand_prefs = [mand_prefs]

for req in mand_prefs:
    req_lower = req.lower()
    if req_lower in ["company", "preferred_company"]:
        trip_request["company"] = st.sidebar.selectbox("Company (Mandatory)", company_options, key="mand_company")
    elif req_lower in ["price_eur", "budget"]:
        trip_request["budget"] = st.sidebar.slider("Max Budget (€) (Mandatory)", 10, 150, 100, step=5, key="mand_budget")
    elif req_lower in ["duration_minutes", "max_duration"]:
        trip_request["max_duration"] = st.sidebar.slider("Max Duration (hours) (Mandatory)", 1, 24, 12, key="mand_duration")
    elif req_lower == "transfers":
        trip_request["max_transfers"] = st.sidebar.slider("Max Transfers (Mandatory)", 0, 3, 2, key="mand_transfers")
    elif req_lower in ["luggage", "max_luggage"]:
        trip_request["max_luggage"] = st.sidebar.selectbox(
            "Required Luggage (Mandatory)", ["2 bags", "3 bags", "4 bags", "5 bags"], key="mand_luggage"
        )
    elif req_lower in ["flexibility", "changeable"]:
        trip_request["flexibility"] = st.sidebar.checkbox(
            "Require Changeable/Flexible Booking (Mandatory)", value=True, key="mand_flexibility"
        )
    elif req_lower in ["stops", "max_stops"]:
        trip_request["max_stops"] = st.sidebar.slider("Max Stops (Mandatory)", 0, 20, 20, key="mand_stops")
   

st.sidebar.markdown("---")

# Optional filters
with st.sidebar.expander("🎯 More Filters (Optional)", expanded=False):
    st.caption("Additional constraint filters for your search:")
    if "company" not in trip_request:
        trip_request["company"] = st.selectbox("Company", company_options, key="reg_company")
    if "budget" not in trip_request:
        trip_request["budget"] = st.slider("Max Budget (€)", 10, 150, 100, step=5, key="reg_budget")
    if "max_duration" not in trip_request:
        trip_request["max_duration"] = st.slider("Max Duration (hours)", 1, 24, 12, key="reg_duration")
    if "max_transfers" not in trip_request:
        trip_request["max_transfers"] = st.slider("Max Transfers", 0, 3, 2, key="reg_transfers")
    if "max_luggage" not in trip_request:
        trip_request["max_luggage"] = st.selectbox(
            "Required Luggage", ["1 bags", "2 bags", "3 bags", "4 bags", "5 bags"], key="reg_luggage"
        )
    if "flexibility" not in trip_request:
        trip_request["flexibility"] = st.checkbox(
            "Require Changeable/Flexible Booking", value=True, key="reg_flexibility"
        )
    if "max_stops" not in trip_request:
        trip_request["max_stops"] = st.slider("Max Stops", 0, 20, 20, key="reg_stops")


#  PAYMENT Section
PAYING_KEY = "paying_offer_id"


def render_payment_form(offer, traveller, offer_id, amount, booking_key):
    with st.form(f"pay_form_{offer_id}"):
        st.markdown(f"**💳 Pay {amount:.2f} €**")
        if getattr(offer, "refundable", False):
            st.caption(f"Cancellation: {offer.refund_advance_pct:g}% refund before travel day, "
                       f"{offer.refund_same_day_pct:g}% on the day.")
        else:
         st.caption("Cancellation: this fare is non-refundable.")
        number = st.text_input("Card number", placeholder="1234 5678 9012 3456")
        c1, c2 = st.columns(2)
        expiry = c1.text_input("Expiry", placeholder="MM/YY")
        cvv = c2.text_input("CVV", type="password", max_chars=4)
        pay = st.form_submit_button("Pay now", type="primary")

    if pay:
        try:
            digits = validate_card(number, expiry, cvv)
            live_offer = offers_by_id.get(offer_id, offer)
            if live_offer.available_seats < 1:
                raise SoldOutError("Sorry, this offer is sold out.")
            booking_id = book_offer(live_offer, traveller)
            live_offer.available_seats -= 1
            log_payment(traveller.id, offer_id, amount, digits)



        except BusBidderError as e:
            log.warning("[%s] %s", e.category, e)
            st.error(str(e))


        except Exception:
            log.exception("Unexpected error while booking %s", offer_id)
            st.error("Something went wrong. Please try again.")
        else:
            st.session_state[booking_key] = booking_id
            st.session_state.pop(PAYING_KEY, None)
            st.rerun()






# MAIN BodY
tab_search, tab_bookings = st.tabs(["🔍 Search Offers", "🎫 My Bookings"])

with tab_search:
    if st.button("🔍 Search", type="primary"):
        trip_req_obj = Trip_Request(
            traveller=traveller,
            destination=trip_request["destination"],
            travel_start_date=trip_request["travel_start_date"].strftime("%Y-%m-%d"),
            travel_end_date=trip_request["travel_end_date"].strftime("%Y-%m-%d"),
            budget=float(trip_request["budget"]),
            max_transfers=int(trip_request["max_transfers"]),
            max_luggage=trip_request["max_luggage"],
            prefered_departure=trip_request["prefered_departure"],
            max_duration=float(trip_request["max_duration"]),
            flexiblity=trip_request["flexibility"],
            preferred_company=trip_request["company"],
            max_stops=trip_request["max_stops"],
        )

        filtered_offers = filter_offers(all_offers, trip_req_obj)
        st.session_state["ranked_results"] = rank_offers(filtered_offers, trip_req_obj)
        st.session_state["search_destination_used"] = trip_request["destination"]
        st.session_state["search_traveller"] = traveller
        # saved here, where it exists, so it survives the reruns from Book / Pay
        st.session_state["search_trip_request"] = trip_req_obj
        st.session_state.pop(PAYING_KEY, None)

    if "ranked_results" in st.session_state:
        ranked_results = st.session_state["ranked_results"]
        search_traveller = st.session_state["search_traveller"]
        search_req = st.session_state["search_trip_request"]

        st.success(
            f"Found **{len(ranked_results)}** matching offers for "
            f"{st.session_state['search_destination_used']} under traveller **{search_traveller.name}**!"
        )

        if ranked_results:
            st.markdown("### 🏆 Top Ranked Offers")
            st.info(explain_top_offer(ranked_results, search_req))

            used_keys = ranking_criteria(search_req)

            for idx, offer in enumerate(ranked_results[:10], start=1):
                get = (lambda k, o=offer: o[k]) if isinstance(offer, dict) else (lambda k, o=offer: getattr(o, k))
                offer_id = get("offer_id")

                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

                    with col1:
                        st.metric(label="Rank", value=f"#{idx}")

                    with col2:
                        st.markdown(f"**{get('company')}** (`{offer_id}`)")
                        st.caption(
                            f"📅 {get('travel_date')} | ⏰ Dep: {get('departure_time')} - Arr: {get('arrival_time')}"
                        )
                        with st.expander("💡 Why this rank?"):
                            st.markdown(explain_offer(offer, idx, ranked_results, search_req))

                    with col3:
                        st.markdown(f"💰 **{get('price_eur'):.2f} €**")
                        st.markdown(
                            f"⏱️ `{get('duration_minutes') / 60:.1f} hrs` | "
                            f"🚏 Stops: {get('stops')} | 🔁 Transfers: {get('transfers')}"
                        )
                        st.caption(
                            f"⭐ {get('customer_rating')} | 🌱 Eco {get('environmental_score')} | "
                            f"🧳 {get('luggage_allowance')} | "
                            f"{'Changeable' if get('changeable') else 'Not changeable'} | "
                            f"{'Refundable' if get('refundable') else 'Non-refundable'}"
                            f"💺 {get('available_seats')} seats left | "
                        )

                        if get("refundable"):
                            st.caption(
                                f"↩️ Cancel before travel date: {get('refund_advance_pct'):g}% refunded | "
                                f"On travel date: {get('refund_same_day_pct'):g}% refunded"
                            )
                        else:
                            st.caption("↩️ Non-refundable")

                    with col4:
                        st.markdown(f"⭐ **Total score: {get('total_score')} / 100**")
                        with st.expander("View criterion scores"):
                            st.dataframe(
                                [
                                    {
                                        "Criterion": LABELS.get(k, k),
                                        "Score": round(v, 1),
                                        "Counts in total": "yes" if k in used_keys else "no",
                                    }
                                    for k, v in get("criterion_scores").items()
                                ],
                                hide_index=True,
                                use_container_width=True,
                            )

                        booking_key = f"booked_{search_traveller.name}_{offer_id}"
                        if st.session_state.get(booking_key):
                            st.success(f"✅ Booked! Ref: {st.session_state[booking_key]}")
                        elif st.session_state.get(PAYING_KEY) == offer_id:
                            render_payment_form(offer, search_traveller, offer_id, get("price_eur"), booking_key)
                        else:
                            if st.button(
                                "Book", type="primary",
                                key=f"book_btn_{search_traveller.name}_{offer_id}",
                            ):
                                st.session_state[PAYING_KEY] = offer_id
                                st.rerun()

                    st.divider()
        else:
            st.warning("No offers matched your exact filter criteria.")

with tab_bookings:
    st.subheader(f"🎫 Bookings for {traveller.name}")

    # message that survives the rerun after a cancellation
    if "cancel_msg" in st.session_state:
        st.success(st.session_state.pop("cancel_msg"))

    my_bookings = get_bookings_for(traveller.id)

    if my_bookings:
        st.caption(f"{len(my_bookings)} booking(s)")

        rows = []
        for b in my_bookings:
            before, on_day = refund_amounts(b)
            if b["refundable"] == "True":
                policy = (f"{float(b['refund_advance_pct']):g}% before travel date / "
                          f"{float(b['refund_same_day_pct']):g}% on travel date")
            else:
                policy = "Non-refundable"

            cancelled = b["status"] == "CANCELLED"
            rows.append({
                "Booking": b["booking_id"],
                "Status": b["status"].title(),
                "Company": b["company"],
                "Travel date": b["travel_date"],
                "Departure": b["departure_time"],
                "Paid (€)": float(b["price_paid_eur"]),
                "Cancellation policy": policy,
                "Refund before travel date (€)": before,
                "Refund on travel date (€)": on_day,
                "Refund if cancelled today (€)": None if cancelled else refund_if_cancelled_today(b),
                "Refunded (€)": float(b["refund_eur"]) if cancelled else None,
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        # cancel a boking 
        active = [b for b in my_bookings if can_cancel(b)]
        if active:
            st.markdown("#### ❌ Cancel a booking")
            labels = {b["booking_id"]: f"{b['booking_id']} | {b['company']} | {b['travel_date']}" for b in active}
            chosen_id = st.selectbox("Select booking", list(labels), format_func=labels.get, key="cancel_select")
            chosen = next(b for b in active if b["booking_id"] == chosen_id)

            refund = refund_if_cancelled_today(chosen)
            paid = float(chosen["price_paid_eur"])
            if chosen["refundable"] == "True":
                st.warning(f"If you cancel now you will be refunded **{refund:.2f} €** of the {paid:.2f} € paid.")
            else:
                st.warning(f"This fare is non-refundable. Cancelling will refund **0.00 €** of the {paid:.2f} € paid.")

            if st.button("Cancel this booking", key="cancel_confirm_btn"):
                try:
                    refunded = cancel_booking(chosen_id, traveller.id)

                    # increase seat
                    live_offer = offers_by_id.get(chosen["offer_id"])
                    if live_offer and live_offer.travel_date == chosen["travel_date"]:
                        live_offer.available_seats += 1
                    # allow the offer to be booked again from the search tab
                    st.session_state.pop(f"booked_{traveller.name}_{chosen['offer_id']}", None)
                    st.session_state["cancel_msg"] = (
                        f"Booking {chosen_id} cancelled. Refund: {refunded:.2f} €."
                    )
                    st.rerun()
                except BusBidderError as e:
                    log.warning("[%s] %s", e.category, e)
                    st.error(str(e))
    else:
        st.info("This traveller has no bookings yet.")