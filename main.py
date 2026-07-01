import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from langchain_core.messages import HumanMessage
from graph import app

st.set_page_config(layout="wide")
st.title("Postcard AI Travel Concierge")

# --- 1. Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. Chat Logic & Dynamic Map Rendering ---
if prompt := st.chat_input("Start planning your trip..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Invoke Graph
    result = app.invoke({"messages": [HumanMessage(content=prompt)]})
    ai_response = result['messages'][-1].content
    
    # Process AI Response
    with st.chat_message("assistant"):
        if "FINAL_PLAN:" in ai_response:
            # Clean and Parse
            json_str = ai_response.replace("FINAL_PLAN:", "").strip()
            try:
                data = json.loads(json_str)
                st.markdown("### Your Curated Itinerary")
                
                # Render 4 Tabs for 4 Combinations
                tabs = st.tabs([c['name'] for c in data['combinations']])
                for i, tab in enumerate(tabs):
                    with tab:
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.write(f"**Logistics:** {data['combinations'][i]['travel_logistics']['suggestion']}")
                            for day in data['combinations'][i].get('days', []):
                                with st.expander(f"Day {day['day']}: {day['plan']}"):
                                    st.write(f"**Insight:** {day.get('insight')}")
                                    st.write(f"**Transport:** {day.get('transport')}")
                        with col2:
                            # Dynamic Map Rendering
                            days = data['combinations'][i]['days']
                            m = folium.Map(location=[days[0]['lat'], days[0]['lon']], zoom_start=12)
                            for d in days:
                                folium.Marker([d['lat'], d['lon']], popup=d['plan']).add_to(m)
                            st_folium(m, width=700, height=500)
            except Exception as e:
                st.error("Error parsing itinerary. Please try again.")
        else:
            # Handle Discovery Questions
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
