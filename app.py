import re
import traceback

import streamlit as st
from offers import create_automated_offers
from models import Traveller, Trip_Request

from filter import filter_offers
from rank import rank_offers
from helper_functions import load_travellers, save_traveller, generate_traveller_id
from constants import BUS_COMPANIES

from booking import book_offer, get_bookings_for

st.set_page_config(page_title="BusBidder Spain", page_icon="🌊", layout="wide")

st.title("🌊 BusBidder Spain")
st.markdown("### Welcome ###")


@st.cache_data
def load_offers():
    return create_automated_offers()


with st.spinner("Generating and loading bus offers..."):
    all_offers = load_offers()

#  SIDEBAR
st.sidebar.header("👤 Traveller Profile")

saved_travellers = load_travellers()
traveller_names = list(saved_travellers.keys())

profile_mode = st.sidebar.radio(
    "Profile Action",
    ["Select Existing Traveller", "Create New Traveller"],
    key="profile_mode_radio",
)

if profile_mode == "Select Existing Traveller":
    selected_name = st.sidebar.selectbox("Choose Traveller", traveller_names, key="select_existing_traveller_box")
    traveller = saved_travellers[selected_name]

    st.sidebar.success(f"Loaded profile: **{traveller.name}**")

else:
    st.sidebar.subheader("Register New Traveller")

    # OUTSIDE the form, so changing it reruns the script and updates the defaults
    traveller_type = st.sidebar.selectbox(
        "Traveller Type",
        ["Business", "Student", "Eco-Conscious"],
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
        "Student": ["Price (€)", "Duration", "Refundable", "Luggage"],
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
            key=f"new_traveller_prefs_{traveller_type}",  
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
                st.success(f"Traveller {cleaned_name} saved successfully! Switch to 'Select Existing Traveller' to use it.")

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

# Optional filters: only shown for fields the profile did NOT already ask for
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
        trip_request["flexibility"] = st.checkbox("Require Changeable/Flexible Booking", value=True, key="reg_flexibility")
    if "max_stops" not in trip_request:
        trip_request["max_stops"] = st.slider("Max Stops", 0, 20, 20, key="reg_stops")

# MAIN BODy 
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

    if "ranked_results" in st.session_state:
        ranked_results = st.session_state["ranked_results"]
        search_traveller = st.session_state["search_traveller"]
        st.success(
            f"Found **{len(ranked_results)}** matching offers for "
            f"{st.session_state['search_destination_used']} under traveller **{search_traveller.name}**!"
        )

        if ranked_results:

            st.markdown("### 🏆 Top Ranked Offers")

            for idx, offer in enumerate(ranked_results[:10], start=1):

                get = (lambda k, o=offer: o[k]) if isinstance(offer, dict) else (lambda k, o=offer: getattr(o, k))
                offer_id = get("offer_id")

                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

                    with col1:
                        st.metric(label="Rank", value=f"#{idx}")
                    with col2:
                        st.markdown(f"**{get('company')}** (`{offer_id}`)")


                        st.caption(f"📅 {get('travel_date')} | ⏰ Dep: {get('departure_time')} - Arr: {get('arrival_time')}")
                    with col3:
                        st.markdown(f"💰 **{get('price_eur'):.2f} €**")
                        st.markdown(f"⏱️ `{get('duration_minutes') / 60:.1f} hrs` | 🚏 Stops: {get('stops')}")
                    with col4:
                        st.markdown(f"⭐ **Mandatory Requirements Score: {get('total_score')} / 100**")
                        with st.expander("View Individual Scores"):
                            for crit, sc in get("criterion_scores").items():
                                st.text(f"{crit}: {sc:.1f}")

                        booking_key = f"booked_{search_traveller.name}_{offer_id}"
                        if st.session_state.get(booking_key, False):
                            st.success("✅ Booked Successfully!")
                        else:
                            if st.button("Book", type="primary", key=f"book_btn_{search_traveller.name}_{offer_id}"):
                                try:
                                    book_offer(offer, search_traveller)
                                    st.session_state[booking_key] = True
                                    st.rerun()



                                except Exception:
                                    st.code(traceback.format_exc())
                    st.divider()
        else:
            st.warning("No offers matched your exact filter criteria.")






with tab_bookings:
    st.subheader(f"🎫 Bookings for {traveller.name}")
    my_bookings = get_bookings_for(traveller.id)

    if my_bookings:
        st.caption(f"{len(my_bookings)} booking(s)")
        st.dataframe(my_bookings, use_container_width=True, hide_index=True)
    else:
        st.info("This traveller has no bookings yet.")