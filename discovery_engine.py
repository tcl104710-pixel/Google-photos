import streamlit as st
import os

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal CSS to maintain dark theme and ensure perfect image clarity
st.markdown("""
<style>
    :root {
        --bg-color: #0f172a;
        --text-primary: #f8fafc;
    }
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', 'Roboto', sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Force tabs to be larger and easier to click */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255,255,255,0.05);
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Google Photos Dashboard")
st.markdown("Navigate through the product intelligence findings using the tabs below. Scroll down to see the full content of each page.")

slide_mapping = {
    "Discovery Overview": "google_photos_retrieval_discovery_overview",
    "Research Dataset": "google_photos_research_dataset",
    "Search Behavior": "google_photos_search_behavior",
    "User Feedback": "google_photos_user_feedback",
    "Retrieval Breaks": "where_google_photos_retrieval_breaks",
    "Opportunities": "evidence_product_opportunities"
}

# --- TABS ---
# Create a tab for each item
tab_names = list(slide_mapping.keys())
tabs = st.tabs(tab_names)

stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"

for i, tab_name in enumerate(tab_names):
    with tabs[i]:
        folder = slide_mapping[tab_name]
        img_path = os.path.join(stitch_dir, folder, "screen.png")
        
        if os.path.exists(img_path):
            # Using native Streamlit image rendering with use_container_width=True.
            # This allows the page to scroll infinitely down, completely eliminating any 
            # bounding box cut-offs while maintaining 100% original clarity!
            st.image(img_path, use_container_width=True)
        else:
            st.error(f"Image not found for {tab_name}.")
