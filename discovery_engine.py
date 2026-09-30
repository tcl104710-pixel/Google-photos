import streamlit as st
import os
from PIL import Image

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean up Streamlit chrome and ensure crisp white background for the content
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {display: none;}
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    /* Style the sidebar to look like the Stitch sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 14px;
        color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# --- VIEW DEFINITIONS ---
views = {
    "Overview": "google_photos_retrieval_discovery_overview",
    "Research Dataset": "google_photos_research_dataset",
    "User Feedback": "google_photos_user_feedback",
    "Search Behavior": "google_photos_search_behavior",
    "Retrieval Failures": "where_google_photos_retrieval_breaks",
    "Evidence & Opportunities": "evidence_product_opportunities"
}

# --- REAL SIDEBAR WITH REAL BUTTONS ---
st.sidebar.image("stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine/google_photos_retrieval_discovery_overview/screen.png", 
                  use_container_width=False, width=30,
                  caption=None) if False else None

st.sidebar.markdown("### 🔍 Google Photos Discovery")
st.sidebar.markdown("*Retrieval Discovery Engine · PM Research*")
st.sidebar.markdown("---")

# Initialize session state
if "current_view" not in st.session_state:
    st.session_state.current_view = "Overview"

# Create a real, clickable button for each view
for view_name in views.keys():
    # Highlight the active view
    if view_name == st.session_state.current_view:
        button_type = "primary"
    else:
        button_type = "secondary"
    
    if st.sidebar.button(view_name, key=f"btn_{view_name}", use_container_width=True, type=button_type):
        st.session_state.current_view = view_name
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Dashboard powered by Stitch Product Intelligence Engine")

# --- MAIN CONTENT: CROPPED IMAGE (sidebar removed) ---
folder = views[st.session_state.current_view]
stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
img_path = os.path.join(stitch_dir, folder, "screen.png")

if os.path.exists(img_path):
    img = Image.open(img_path)
    w, h = img.size
    
    # Crop out the left sidebar (approx 235px) from the original 1600px image
    # This removes the drawn-on sidebar so we don't have duplicate navigation
    cropped = img.crop((235, 0, w, h))
    
    # Display the cropped content at full width — no height restrictions, fully scrollable
    st.image(cropped, use_container_width=True)
else:
    st.error(f"Image not found for '{st.session_state.current_view}'.")