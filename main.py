import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from graph import app

st.set_page_config(layout="wide")
st.title("Postcard AI Travel Concierge")

# --- Sidebar ---
with st.sidebar:
    st.header("Plan your trip")
    dest = st.text_input("Destination")
    t_date = st.date_input("Travel Date")
    feed = st.text_area("Preferences")
    if st.button("Generate Plan"):
        st.session_state.last_result = app.invoke({
            "itinerary": {"destination": dest, "nodes": []},
            "travel_date": str(t_date),
            "feedback": [feed]
        })
        st.session_state.selected_node = None 
with st.sidebar:
    st.header("Trip Configuration")
    dest = st.text_input("Destination")
    budget = st.slider("Budget Range (₹)", 10000, 500000, 50000)
    
    mode = st.selectbox("How are you reaching?", ["Flight", "Bus", "Driving"])
    
    # Conditional Inputs
    if mode == "Driving":
        arr_date = st.date_input("Arrival Date")
        arr_time = st.time_input("Arrival Time")
        dep_date = st.date_input("Departure Date")
    else:
        t_date = st.date_input("Travel Date")
        
    if st.button("Curate 4 Trip Combinations"):
        # Invoke agent with full context
        st.session_state.last_result = app.invoke({
            "itinerary": {"destination": dest, "nodes": []},
            "logistics": {"mode": mode, "budget": budget},
            "feedback": [f"Need 4 combinations for {mode} travel"]
        })
# --- Main UI ---
if 'last_result' in st.session_state:
    nodes = st.session_state.last_result['itinerary'].get('nodes', [])
    if nodes:
        # 1:2 layout gives the map more room
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Curated Recommendations")
            for node in nodes:
                status = "✅ Open" if node.get('is_open_on_date') else "❌ Closed"
                if st.button(f"View {node.get('name')}", key=node.get('name')):
                    st.session_state.selected_node = node
                
                with st.expander(f"{node.get('name')} {status}"):
                    st.write(f"**Category:** {node.get('category')}")
                    st.write(f"**Hours:** {node.get('weekday_hours')}")
                    st.write(f"**Transport:** {node.get('transport_options')}")
                    st.info(f"**Tip:** {node.get('transport_tip')}")
        
        with col2:
            st.subheader("Itinerary Map")
            m = folium.Map(location=[nodes[0]['lat'], nodes[0]['lng']], zoom_start=13)
            for node in nodes:
                is_selected = 'selected_node' in st.session_state and st.session_state.selected_node and st.session_state.selected_node['name'] == node['name']
                folium.Marker(
                    [node['lat'], node['lng']], 
                    popup=node['name'],
                    icon=folium.Icon(color="blue" if is_selected else "red")
                ).add_to(m)
            st_folium(m, width=1000, height=600)
