import streamlit as st
from models import Traveller, Trip_Request
from offers import create_automated_offers
from filter import filter_offers
from rank import rank_offers
from helper_functions import load_travellers, save_traveller
import re
from constants import BUS_COMPANIES

# Page Configuration
st.set_page_config(
    page_title="BusBidder Spain",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 BusBidder Spain")
st.markdown("### Welcome ###")

# Cache the ui for rendering purposes
@st.cache_data
def load_offers():
    return create_automated_offers()


with st.spinner("Generating and loading bus offers..."):
    all_offers = load_offers()

# sidBar
st.sidebar.header("👤 Traveller Profile")


saved_travellers = load_travellers()
traveller_names = list(saved_travellers.keys())


profile_mode = st.sidebar.radio("Profile Action", ["Select Existing Traveller", "Create New Traveller"], key="profile_mode_radio")

if profile_mode == "Select Existing Traveller":
    selected_name = st.sidebar.selectbox("Choose Traveller", traveller_names, key="select_existing_traveller_box")
    traveller = saved_travellers[selected_name]
    st.sidebar.success(f"Loaded profile: **{traveller.name}**")

else:
    with st.sidebar.form("new_traveller_form"):
        st.subheader("Register New Traveller")
        name = st.text_input("Name", key="new_traveller_name")
        age = st.number_input("Age", min_value=1, max_value=120, value=25, key="new_traveller_age")
        gender = st.selectbox("Gender", ["M", "F", "Other"], key="new_traveller_gender")
        phone = st.text_input("Phone", value="943XXXXX", key="new_traveller_phone")
        email = st.text_input("Email", value="user@gmail.com", key="new_traveller_email")
        traveller_type = st.selectbox("Traveller Type", ["Business", "Student", "Eco-Conscious"], key="new_traveller_type")
        
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
            "Luggage": "max_luggage"
        }
        
        selected_pref_labels = st.multiselect(
            "Mandatory Ranking Preferences:",
            options=list(available_prefs.keys()),
            default=["Company", "Price (€)", "Transfers", "Duration"],
            key="new_traveller_prefs"
        )
        submitted = st.form_submit_button("Save Traveller")

        if submitted:
            # regex
            name_pattern = r"^[A-Za-zÀ-ÿ\s]{2,40}$"                  
            phone_pattern = r"^(\+34|0034)?[6-9]\d{8}$"           
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"           

            cleaned_name = name.strip()
            cleaned_phone = phone.strip()
            cleaned_email = email.strip()

            # regex validation
            if not re.match(name_pattern, cleaned_name):
                 st.error("Invalid Name: Must contain only letters and spaces (2 to 40 characters maximum and no numbers).")
            elif not re.match(email_pattern, cleaned_email):
                st.error("Invalid Email: Please enter a valid email address (ex: user@gmail.com).")
            elif not re.match(phone_pattern, cleaned_phone):
                 st.error("Invalid Phone: Please enter a valid phone number.")


            else:
                new_traveller = Traveller(
                    name=name, age=age, gender=gender, phone=phone, email=email,
                    traveller_type=traveller_type,
                    mandatory_preferences=[available_prefs[pref] for pref in selected_pref_labels]
                )
                save_traveller(new_traveller)
                st.success(f"Traveller {name} saved successfully! Please restart or refresh the view.")
                st.rerun()
        
    

    traveller = saved_travellers[traveller_names[0]]

trip_request = {}
more_filters_fields ={}

destinations_list = sorted(list(set(o.destination for o in all_offers)))

st.sidebar.subheader("🔍 Search")
trip_request["destination"] = st.sidebar.selectbox("Destination", destinations_list)
trip_request["travel_start_date"] = st.sidebar.date_input("Travel Start Date (Mandatory)", key="mand_start_date")
trip_request["travel_end_date"] = st.sidebar.date_input("Travel End Date (Mandatory)", key="mand_end_date")
trip_request["prefered_departure"] = st.sidebar.selectbox("Preferred Departure Time Window (Mandatory)", ["Morning", "AfterNoon", "Evening", "Night"], key="mand_departure")

company_options = ["None"] + [comp.name for _, comp in BUS_COMPANIES.items()]
st.sidebar.markdown("---")
st.sidebar.subheader("🎯User Mandatory Preference Filters")
st.sidebar.caption("Criteria selected in your profile for scoring and ranking:")





mand_prefs = getattr(traveller, "mandatory_preferences", [])
if isinstance(mand_prefs, str):
    mand_prefs = [mand_prefs]

# 1. Mandatory Filter inputs based on traveller profile preferences
for req in mand_prefs:
    req_lower = req.lower()
    if req_lower in ["company", "preferred_company"]:
        trip_request["company"] = st.sidebar.selectbox("Company (Mandatory)",company_options, key="mand_company")
    elif req_lower in ["price_eur", "budget"]:
        trip_request["budget"] = st.sidebar.slider("Max Budget (€) (Mandatory)", min_value=10, max_value=150, value=100, step=5, key="mand_budget")
    elif req_lower in ["duration_minutes", "max_duration"]:
        trip_request["max_duration"] = st.sidebar.slider("Max Duration (hours) (Mandatory)", min_value=1, max_value=24, value=12, key="mand_duration")
    elif req_lower == "transfers":
        trip_request["max_transfers"] = st.sidebar.slider("Max Transfers (Mandatory)", min_value=0, max_value=3, value=2, key="mand_transfers")
    elif req_lower in ["luggage", "max_luggage"]:
        trip_request["max_luggage"] = st.sidebar.selectbox("Required Luggage (Mandatory)", ["2 bags", "3 bags", "4 bags", "5 bags"], key="mand_luggage")
    elif req_lower in ["flexibility", "changeable"]:
        trip_request["flexibility"] = st.sidebar.checkbox("Require Changeable/Flexible Booking (Mandatory)", value=True, key="mand_flexibility")
    elif req_lower in ["stops","max_stops"]:
        st.sidebar.slider("Max Stops", min_value=0, max_value=20, value=20, key="mand_stops")



st.sidebar.markdown("---")
st.sidebar.subheader("🎯 More Filters")
st.sidebar.caption("Additional constraint filters for your search:")


if st.sidebar.expander("🎯 More Filters (Optional)", expanded=False):
    if "company" not in trip_request:
     trip_request["company"] = st.sidebar.selectbox("Company", [comp.name for _, comp in BUS_COMPANIES.items()], key="reg_company")
     more_filters_fields["company"] = [comp.name for _,comp in BUS_COMPANIES.items()]
    if "budget" not in trip_request:
        trip_request["budget"] = st.sidebar.slider("Max Budget (€)", min_value=10, max_value=150, value=100, step=5, key="reg_budget")
        more_filters_fields["budget"] = trip_request["budget"]
    if "max_duration" not in trip_request:
        trip_request["max_duration"] = st.sidebar.slider("Max Duration (hours)", min_value=1, max_value=24, value=12, key="reg_duration")
        more_filters_fields["max_duration"] = trip_request["max_duration"]
    if "max_transfers" not in trip_request:
        trip_request["max_transfers"] = st.sidebar.slider("Max Transfers", min_value=0, max_value=3, value=2, key="reg_transfers")
        more_filters_fields["max_transfers"] = trip_request["max_transfers"]
    if "max_luggage" not in trip_request:
        trip_request["max_luggage"] = st.sidebar.selectbox("Required Luggage", ["1 bags","2 bags", "3 bags", "4 bags", "5 bags"], key="reg_luggage")
        more_filters_fields["max_luggage"] = trip_request["max_luggage"]
    if "flexibility" not in trip_request:
        trip_request["flexibility"] = st.sidebar.checkbox("Require Changeable/Flexible Booking", value=True, key="reg_flexibility")
        more_filters_fields["flexibility"] = trip_request["flexibility"]
    if "max_stops" not in trip_request:
        trip_request["max_stops"]= st.sidebar.slider("Max Stops", min_value=0, max_value=20, value=20, key="reg_stops")
        more_filters_fields["max_stops"] = trip_request["max_stops"]

# print(more_filters_fields)
# MAIN CONTENT AREA
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
        max_stops=trip_request["max_stops"]
    )

    filtered_offers = filter_offers(all_offers, trip_req_obj)
    ranked_results = rank_offers(filtered_offers, trip_req_obj)





    st.success(f"Found **{len(ranked_results)}** matching offers for {trip_request['destination']} under traveler **{traveller.name}**!")

    if ranked_results:
        st.markdown("### 🏆 Top Ranked Offers")
        for idx, offer in enumerate(ranked_results[:10], start=1):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                with col1:
                    st.metric(label="Rank", value=f"#{idx}")
                with col2:
                    company_name = offer["company"] if isinstance(offer, dict) else offer.company
                    offer_id = offer["offer_id"] if isinstance(offer, dict) else offer.offer_id
                    travel_date = offer["travel_date"] if isinstance(offer, dict) else offer.travel_date
                    dep_time = offer["departure_time"] if isinstance(offer, dict) else offer.departure_time
                    arr_time = offer["arrival_time"] if isinstance(offer, dict) else offer.arrival_time
                    
                    st.markdown(f"**{company_name}** (`{offer_id}`)")
                    st.caption(f"📅 {travel_date} | ⏰ Dep: {dep_time} - Arr: {arr_time}")
                with col3:
                    price = offer["price_eur"] if isinstance(offer, dict) else offer.price_eur
                    duration = offer["duration_minutes"] if isinstance(offer, dict) else offer.duration_minutes
                    stops = offer["stops"] if isinstance(offer, dict) else offer.stops
                    
                    st.markdown(f"💰 **{price:.2f} €**")
                    st.markdown(f"⏱️ `{duration/60:.1f} hrs` | 🚏 Stops: {stops}")
                with col4:
                    score = offer["total_score"] if isinstance(offer, dict) else offer.total_score
                    scores_dict = offer["criterion_scores"] if isinstance(offer, dict) else offer.criterion_scores
                    
                    st.markdown(f"⭐ **Mandatory Requirements Score: {score} / 100**")
                    with st.expander("View Individual Scores"):
                        for crit, sc in scores_dict.items():
                            st.text(f"{crit}: {sc:.1f}")
                    st.button("Book", type="primary",key={idx})
                st.divider()
    # elif more_filters_offers:
    #             st.markdown("### 🏆 Top Ranked Offers")
    #             for idx, offer in enumerate(ranked_results[:10], start=1):
    #                 with st.container():
    #                     col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
    #                     with col1:
    #                         st.metric(label="Rank", value=f"#{idx}")
    #                     with col2:
    #                         company_name = offer["company"] if isinstance(offer, dict) else offer.company
    #                         offer_id = offer["offer_id"] if isinstance(offer, dict) else offer.offer_id
    #                         travel_date = offer["travel_date"] if isinstance(offer, dict) else offer.travel_date
    #                         dep_time = offer["departure_time"] if isinstance(offer, dict) else offer.departure_time
    #                         arr_time = offer["arrival_time"] if isinstance(offer, dict) else offer.arrival_time
                            
    #                         st.markdown(f"**{company_name}** (`{offer_id}`)")
    #                         st.caption(f"📅 {travel_date} | ⏰ Dep: {dep_time} - Arr: {arr_time}")
    #                     with col3:
    #                         price = offer["price_eur"] if isinstance(offer, dict) else offer.price_eur
    #                         duration = offer["duration_minutes"] if isinstance(offer, dict) else offer.duration_minutes
    #                         stops = offer["stops"] if isinstance(offer, dict) else offer.stops
                            
    #                         st.markdown(f"💰 **{price:.2f} €**")
    #                         st.markdown(f"⏱️ `{duration/60:.1f} hrs` | 🚏 Stops: {stops}")
    #                     with col4:
    #                         score = offer["total_score"] if isinstance(offer, dict) else offer.total_score
    #                         scores_dict = offer["criterion_scores"] if isinstance(offer, dict) else offer.criterion_scores
                            
    #                         st.markdown(f"⭐ **Mandatory Requirements Score: {score} / 100**")
    #                         with st.expander("View Criteria Scores"):
    #                             for crit, sc in scores_dict.items():
    #                                 st.text(f"{crit}: {sc:.1f}")
    #                     st.divider()
        
    
    else:
        st.warning("No offers matched your exact filter criteria.")