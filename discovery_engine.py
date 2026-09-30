import streamlit as st
import os
from PIL import Image

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium styling: hide sidebar toggle, Streamlit chrome, and style the nav panel
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    header {display: none !important;}
    
    /* Hide the sidebar collapse control completely */
    [data-testid="collapsedControl"] {display: none !important;}
    
    /* Remove default page padding for full-width content */
    .block-container {
        padding: 0.5rem 1rem 1rem 1rem !important;
        max-width: 100% !important;
    }
    
    /* Style the navigation buttons */
    .nav-container {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
        padding: 1rem 0.75rem;
        border-radius: 8px;
        height: 100%;
        min-height: 90vh;
    }
    .nav-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.25rem;
    }
    .nav-subtitle {
        font-size: 0.75rem;
        color: #718096;
        margin-bottom: 1.5rem;
    }
    
    /* Make buttons look like nav items */
    div[data-testid="column"]:first-child .stButton > button {
        width: 100%;
        text-align: left;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        border: none;
        margin-bottom: 2px;
        transition: all 0.15s ease;
    }
    div[data-testid="column"]:first-child .stButton > button[kind="secondary"] {
        background: transparent;
        color: #4a5568;
    }
    div[data-testid="column"]:first-child .stButton > button[kind="secondary"]:hover {
        background: #f7fafc;
        color: #2d3748;
    }
    div[data-testid="column"]:first-child .stButton > button[kind="primary"] {
        background: #1a73e8;
        color: white;
    }
    
    /* Ensure the content image is crisp */
    div[data-testid="column"]:nth-child(2) .stImage > img {
        border-radius: 0;
        image-rendering: -webkit-optimize-contrast;
    }
</style>
""", unsafe_allow_html=True)

# --- VIEW DEFINITIONS ---
# Each entry: display_name -> (folder, crop_left_px)
# crop_left_px = exact pixel to crop the drawn sidebar from the original image
views = {
    "📊 Overview": ("google_photos_retrieval_discovery_overview", 380),
    "📁 Research Dataset": ("google_photos_research_dataset", 370),
    "💬 User Feedback": ("google_photos_user_feedback", 180),
    "🔍 Search Behavior": ("google_photos_search_behavior", 178),
    "⚠️ Retrieval Failures": ("where_google_photos_retrieval_breaks", 350),
    "💡 Evidence & Opportunities": ("evidence_product_opportunities", 395),
}

# Initialize session state
if "current_view" not in st.session_state:
    st.session_state.current_view = "📊 Overview"

# --- LAYOUT: Fixed nav column + content column ---
nav_col, content_col = st.columns([1, 5], gap="small")

# LEFT NAVIGATION PANEL (static, no collapse/expand)
with nav_col:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<p class="nav-title">🔍 Google Photos Discovery</p>', unsafe_allow_html=True)
    st.markdown('<p class="nav-subtitle">Retrieval Discovery Engine · PM Research</p>', unsafe_allow_html=True)
    
    for view_name in views.keys():
        btn_type = "primary" if view_name == st.session_state.current_view else "secondary"
        if st.button(view_name, key=f"btn_{view_name}", use_container_width=True, type=btn_type):
            st.session_state.current_view = view_name
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# RIGHT CONTENT PANEL
with content_col:
    folder, crop_left = views[st.session_state.current_view]
    stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
    img_path = os.path.join(stitch_dir, folder, "screen.png")
    
    if os.path.exists(img_path):
        img = Image.open(img_path)
        w, h = img.size
        
        # Crop out the drawn sidebar from the left edge
        # Also crop the bottom "Dataset" info box if present (it's in the sidebar area, < crop_left)
        cropped = img.crop((crop_left, 0, w, h))
        
        # Display at full container width — naturally scrollable, no height restrictions
        st.image(cropped, use_container_width=True)
    else:
        st.error(f"Image not found for '{st.session_state.current_view}'.")