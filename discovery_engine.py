import streamlit as st
import os

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make images fit nicely and look premium
st.markdown("""
<style>
    /* Dark mode premium theme */
    :root {
        --bg-color: #0f172a;
        --text-primary: #f8fafc;
    }
    
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', 'Roboto', sans-serif;
    }
    
    /* Hide some default Streamlit elements for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Ensure images fit nicely in the frame without massive scrolling */
    .stImage > img {
        max-height: 85vh;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🔍 Google Photos Dashboard")
st.sidebar.markdown("Navigate through the product intelligence findings.")

slide_mapping = {
    "Discovery Overview": "google_photos_retrieval_discovery_overview",
    "Research Dataset": "google_photos_research_dataset",
    "Search Behavior": "google_photos_search_behavior",
    "User Feedback": "google_photos_user_feedback",
    "Where Retrieval Breaks": "where_google_photos_retrieval_breaks",
    "Product Opportunities": "evidence_product_opportunities"
}

# Dynamic selection
selected_view = st.sidebar.radio(
    "Select Dashboard View:",
    list(slide_mapping.keys())
)

st.sidebar.markdown("---")
st.sidebar.info("This dashboard presents evidence-backed insights regarding how users search for photos and where the current system fails.")

# --- MAIN FRAME ---
st.title(selected_view)

stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
folder = slide_mapping[selected_view]
img_path = os.path.join(stitch_dir, folder, "screen.png")

if os.path.exists(img_path):
    # Display the image dynamically based on selection, fitting the container
    st.image(img_path, use_container_width=True)
else:
    st.error(f"Image not found for {selected_view}. Expected at: {img_path}")
