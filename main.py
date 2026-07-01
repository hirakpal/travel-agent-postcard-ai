import streamlit as st
import folium
from streamlit_folium import st_folium
from graph import app

st.set_page_config(layout="wide")
st.title("Postcard AI Travel Concierge")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Trip Configuration")
    dest = st.text_input("Destination", key="dest_input")
    budget = st.slider("Budget (₹)", 10000, 500000, 50000, key="budget_slider")
    mode = st.selectbox("How are you reaching?", ["Flight", "Bus", "Driving"], key="mode_select")
    
    if st.button("Generate My Plans"):
        st.session_state.last_result = app.invoke({
            "itinerary": {"destination": dest},
            "logistics": {"mode": mode, "budget": budget}
        })

# --- Main Dashboard ---
if 'last_result' in st.session_state:
    combinations = st.session_state.last_result['itinerary'].get('combinations', [])
    if combinations:
        tabs = st.tabs([c['name'] for c in combinations])
        for i, tab in enumerate(tabs):
            with tab:
                st.subheader(f"Logistics Suggestion: {combinations[i]['travel_logistics']['suggestion']}")
                col1, col2 = st.columns([1, 2])
                with col1:
                    for day in combinations[i].get('days', []):
                        with st.expander(f"Day {day['day']}: {day['plan']}"):
                            st.write(f"**Insight:** {day.get('insight', 'No insight available.')}")
                            st.write(f"**Transport:** {day.get('transport')}")
                with col2:
                    # Map Rendering
                    m = folium.Map(location=[combinations[i]['days'][0]['lat'], combinations[i]['days'][0]['lon']], zoom_start=12)
                    for day in combinations[i].get('days', []):
                        folium.Marker([day['lat'], day['lon']], popup=day['plan']).add_to(m)
                    st_folium(m, width=800, height=500)
