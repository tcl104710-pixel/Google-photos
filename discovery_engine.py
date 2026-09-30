import streamlit as st
import os
import base64

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Google Photos Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Completely remove all Streamlit padding, headers, footers, and margins
# so the image fills the entire screen like a native web app!
st.markdown("""
<style>
    .stApp > header {display: none;}
    .block-container {
        padding: 0rem !important; 
        max-width: 100% !important;
        background-color: #ffffff;
    }
    footer {display: none;}
    
    /* Ensure no scrollbars exist from streamlit margins */
    body {
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Define the views and their corresponding folders
views = [
    "Overview",
    "Dataset",
    "Feedback",
    "Behavior",
    "Failures",
    "Opportunities"
]

folders = [
    "google_photos_retrieval_discovery_overview",
    "google_photos_research_dataset",
    "google_photos_user_feedback",
    "google_photos_search_behavior",
    "where_google_photos_retrieval_breaks",
    "evidence_product_opportunities"
]

# Get the current view from the URL query parameter (defaults to Overview)
current_view = st.query_params.get("view", "Overview")
if current_view not in views:
    current_view = "Overview"

view_index = views.index(current_view)
folder = folders[view_index]
stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
img_path = os.path.join(stitch_dir, folder, "screen.png")

if os.path.exists(img_path):
    # Read the image and convert to Base64
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        
    # We create an SVG image map overlaid EXACTLY on top of the fake buttons in the image.
    # When the user clicks the fake button on the PNG, they actually click an invisible HTML link
    # that reloads the Streamlit app with the new query parameter!
    
    # We use generous bounding boxes to ensure clicks register perfectly.
    y_start = 425
    y_step = 85
    
    rects = ""
    for i, v in enumerate(views):
        rects += f'<a target="_self" href="/?view={v.replace(" ", "%20")}"><rect x="30" y="{y_start + i*y_step}" width="370" height="{y_step}" fill="transparent" style="cursor: pointer;" /></a>\n'

    # Render the interactive image seamlessly
    html_code = f'''
    <div style="position: relative; width: 100%; max-width: 1600px; margin: 0 auto; background-color: #ffffff;">
        <svg viewBox="0 0 1600 1907" style="position: absolute; top: 0; left: 0; width: 100%; height: auto; z-index: 10;">
            {rects}
        </svg>
        <img src="data:image/png;base64,{encoded_string}" style="width: 100%; height: auto; display: block;" />
    </div>
    '''
    st.markdown(html_code, unsafe_allow_html=True)
else:
    st.error(f"Image not found.")
