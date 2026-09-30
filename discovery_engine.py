import streamlit as st
import os
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remove all Streamlit padding, headers, footers, and margins
st.markdown("""
<style>
    .stApp > header {display: none;}
    .block-container {
        padding: 0rem !important; 
        max-width: 100% !important;
        background-color: #ffffff;
    }
    footer {display: none;}
</style>
""", unsafe_allow_html=True)

views = [
    "Overview",
    "Dataset",
    "Behavior",
    "Feedback",
    "Failures",
    "Opportunities"
]

folders = [
    "google_photos_retrieval_discovery_overview",
    "google_photos_research_dataset",
    "google_photos_search_behavior",
    "google_photos_user_feedback",
    "where_google_photos_retrieval_breaks",
    "evidence_product_opportunities"
]

# State management for view navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Overview"

view_index = views.index(st.session_state.current_view)
folder = folders[view_index]
stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
img_path = os.path.join(stitch_dir, folder, "screen.png")

if os.path.exists(img_path):
    # This renders the image seamlessly natively and captures clicks!
    # use_column_width=True ensures it scales cleanly across the screen without cropping.
    value = streamlit_image_coordinates(
        img_path,
        key=f"img_{st.session_state.current_view}",
        use_column_width=True
    )

    # Process clicks
    if value is not None:
        # We need to map the clicked X, Y back to original image dimensions
        # streamlit-image-coordinates returns absolute pixel coordinates of the original image!
        # Original width is 1600.
        x = value["x"]
        y = value["y"]
        
        # Check if click is in the left sidebar area (x < 370)
        if x < 370:
            # Map Y coordinate to a button
            if 390 <= y <= 475:
                st.session_state.current_view = "Overview"
                st.rerun()
            elif 476 <= y <= 560:
                st.session_state.current_view = "Dataset"
                st.rerun()
            elif 561 <= y <= 645:
                st.session_state.current_view = "Behavior"
                st.rerun()
            elif 646 <= y <= 730:
                st.session_state.current_view = "Feedback"
                st.rerun()
            elif 731 <= y <= 815:
                st.session_state.current_view = "Failures"
                st.rerun()
            elif 816 <= y <= 900:
                st.session_state.current_view = "Opportunities"
                st.rerun()
else:
    st.error(f"Image not found.")
