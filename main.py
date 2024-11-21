# main.py

import streamlit as st
import io
from datetime import datetime
import boto3

# Import custom modules
from recording import handle_recording
from uploader import handle_uploader
from display_buttons import handle_display_buttons

# =============================================
# 1. Set Page Configuration First
# =============================================
st.set_page_config(
    page_title="Medical Transcription",
    page_icon="👨‍⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# 2. Initialize Session State Variables
# =============================================
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = io.BytesIO()

if "transcription_text" not in st.session_state:
    st.session_state.transcription_text = ""

if "show_buttons" not in st.session_state:
    st.session_state.show_buttons = False

if "upload_counter" not in st.session_state:
    st.session_state.upload_counter = 0

if "timestamp" not in st.session_state:
    st.session_state.timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

if "recording" not in st.session_state:
    st.session_state.recording = False

if 'paused' not in st.session_state:
    st.session_state.paused = False

# =============================================
# 3. Define Placeholders and Variables
# =============================================
# Define the transcription_placeholder after set_page_config
transcription_placeholder = st.empty()

# Use the session ID from session state
timestamp = st.session_state.timestamp

# Define the S3 bucket, folder, and file name
bucket_name = 'ai.hadassah'
folder_name = f"{timestamp}"
file_name = 'raw.txt'

# Initialize the S3 client with the correct region
s3_client = boto3.client('s3', region_name='us-east-1')  # Ensure this matches your S3 bucket's region

# =============================================
# 4. Apply Custom CSS for Styling
# =============================================
# Modern clinical theme CSS
st.markdown("""
    <style>
        /* Clinical color palette */
        :root {
            --primary-blue: #E3F2FD;    /* Light blue background */
            --secondary-blue: #90CAF9;   /* Accent blue */
            --dark-blue: #1976D2;        /* Text and button blue */
            --white: #FFFFFF;            /* Pure white */
            --gray: #F5F5F5;             /* Light gray for sections */
        }

        /* Global styles */
        .stApp {
            background-color: var(--primary-blue);
        }

        .main {
            background-color: var(--white);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        /* Header styling */
        h1 {
            color: var(--dark-blue);
            font-family: 'Heebo', sans-serif;
            text-align: right;
            padding: 1rem 0;
            border-bottom: 3px solid var(--secondary-blue);
        }

        /* Text areas */
        .stTextArea>div>div>textarea {
            background-color: var(--white);
            border: 2px solid var(--secondary-blue);
            border-radius: 10px;
            padding: 1rem;
            direction: rtl;
            text-align: right;
            font-family: 'Heebo', sans-serif;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        /* Buttons */
        .stButton>button {
            background-color: var(--dark-blue);
            color: var(--white);
            border-radius: 25px;
            padding: 0.5rem 2rem;
            font-family: 'Heebo', sans-serif;
            border: none;
            transition: all 0.3s ease;
            width: 100%;
            margin: 0.5rem 0;
        }

        .stButton>button:hover {
            background-color: var(--secondary-blue);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Control panel */
        .control-panel {
            background-color: var(--gray);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            direction: rtl;
        }

        /* Success messages */
        .stSuccess {
            background-color: #E8F5E9;
            border: none;
            border-radius: 10px;
            padding: 1rem;
            text-align: right;
            direction: rtl;
        }

        /* Error messages */
        .stError {
            background-color: #FFEBEE;
            border: none;
            border-radius: 10px;
            padding: 1rem;
            text-align: right;
            direction: rtl;
        }

        /* RTL support for all text */
        .element-container, .stMarkdown, p {
            direction: rtl;
            text-align: right;
        }

        /* Button icons */
        .button-icon {
            font-size: 1.5rem;
            margin-left: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 5. Define the S3 Key for raw.txt
# =============================================
raw_text_key = f"{folder_name}/raw.txt"

# =============================================
# 6. App Header
# =============================================

# Inject Custom CSS to Reduce Top Padding
st.markdown(
    """
    <style>
    /* Adjust the top padding of the main content container */
    .block-container {
        padding-top: 1rem; /* Reduce this value to move the header upwards */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App Header Content with RTL Alignment
# App Header Content with RTL Alignment
st.markdown(
    """
    <h1 style='text-align: right; color: #333333;' dir='rtl'>👨‍⚕️ הדסה - מערכת תמלול רפואי חכמה</h1>
    
    """,
    unsafe_allow_html=True
)

# Add a blank line using <br> tags
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <p class='subtitle' style='text-align: right; color: #555555;' dir='rtl'>מערכת תמלול מתקדמת לשימוש הצוות הרפואי</p>
    <p class='subtitle' style='text-align: right; color: #555555;' dir='rtl'>ניתן לבצע הקלטה של השיחה או להעלות קובץ אודיו מוכן</p>
    <p class='subtitle' style='text-align: right; color: #555555;' dir='rtl'>המערכת יודע לתמלל דו שיח בין רופא לחולה, לתקן את הטקסט ולסכם אותו</p>
    <p class='subtitle' style='text-align: right; color: #555555;' dir='rtl'>ניתן לערוך ולעדכן את הסיכום לאחר הצגתו</p>
    """,
    unsafe_allow_html=True
)


# =============================================
# 7. Create Control Panel Layout
# =============================================
st.markdown("<div class='control-panel'>", unsafe_allow_html=True)

st.markdown("<p class='subtitle'>בחרו אחד משתי האפשרויות הבאות - העלאת קובץ אודיו או התחל הקלטה </p>", unsafe_allow_html=True)

#################################### 1st Option: Play and Transcribe Text ########################################

# Handle Recording (Start & Stop)
handle_recording(folder_name, bucket_name)

# Handle File Upload via Checkbox
handle_uploader(folder_name, bucket_name)

# Handle Displaying Transcription Buttons
handle_display_buttons(folder_name, bucket_name)

# Close the control panel div
st.markdown("</div>", unsafe_allow_html=True)
