import streamlit as st
import cv2
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt
from PIL import Image
import sys
import os
import ssl
# --------------------------------------
# Configuration
# --------------------------------------

# Set page configuration
st.set_page_config(
    page_title="CCTV SMA N 1 Salatiga",
    page_icon="📷",
    layout="wide",
)

# File paths
USERS_CSV_PATH = 'users.csv'
CAMERAS_CSV_PATH = 'cameras.csv'


# Load user credentials from CSV
def load_user_credentials():
    df = pd.read_csv(USERS_CSV_PATH)
    return {row['username']: row['password'] for _, row in df.iterrows()}


# Load camera streams (now as MQTT topics) from CSV
def load_camera_streams():
    df = pd.read_csv(CAMERAS_CSV_PATH)
    return {row['name']: row['url'] for _, row in df.iterrows()}


# --------------------------------------
# Helper Functions
# --------------------------------------

def authenticate(username, password):
    credentials = load_user_credentials()
    return credentials.get(username) == password


# MQTT setup for receiving frames
import paho.mqtt.client as mqtt
import numpy as np
import cv2
import ssl


class MqttReceiver:
    def __init__(self, topic):
        self.broker = "broker.mqtt-dashboard.com"  # Ganti dengan alamat broker MQTT Anda
        self.port = 1883  # Port untuk SSL/TLS
        self.username = "sman1"  # Ganti dengan username Anda
        self.password = "SMAN1Salatiga"  # Ganti dengan password Anda
        self.topic = topic
        self.frame = None

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)

        # Konfigurasi SSL/TLS
        # self.client.tls_set(ca_certs=resource_path("isrgrootx1.pem"))  # Ganti dengan path ke file sertifikat CA Anda
        # self.client.tls_insecure_set(False)

        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            nparr = np.frombuffer(msg.payload, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is not None:
                self.frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                print("Received empty or invalid image")

        except Exception as e:
            print(f"Error processing message: {e}")

    def get_frame(self):
        return self.frame

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


def initial_check(mqtt_receivers):
    offline_cameras = []
    for camera_name, receiver in mqtt_receivers.items():
        if receiver.get_frame() is None:
            offline_cameras.append(camera_name)
    return offline_cameras


def login_page():
    hide_streamlit_style = """
    <style>
        [data-testid="stHeader"] {
            display: none;
        }
        footer {
            display: none;
        }
        .main {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.title("🔒 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if authenticate(username, password):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password")


def dashboard(mqtt_receivers):
    hide_streamlit_style = """
    <style>
       [data-testid="stHeader"] {
            display: none;
        }

        footer {
            display: none;
        }
        .main {
            margin-top: 4rem !important;
            padding-top: 0 !important;
        }
        .e1f1d6gn4{
            margin-top: 0 !important;
        }
        .ea3mdgi5{
            padding: 0rem 1.2rem 10rem !important;
        }
        h1 {
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 700;
            padding: 0rem 0px 1rem;
            padding-bottom: 40px !important;
            margin: 0px;
            line-height: 1.2;
        }
        .st-bv {
            margin-bottom: 20px;
        }
        .streamlit-footer {
            display: none;
        }
        .e1f1d6gn2{
            gap: 0rem !important;
        }
        .stButton {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .ef3psqc5{
            left: 1rem !important;
            margin: 0px 0px !important;
            justify-content: left !important;
        }
        .eczjsme5{
            left: 1rem !important;
        }
        
        .e115fcil2{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
        }
        
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.title("CCTV SMA N 1 Salatiga")

    # Sidebar for navigation
    logo = Image.open(resource_path('logo.png'))
    st.sidebar.image(logo, width=150)
    st.sidebar.title("Menu")

    # Stop running any previous loops
    st.session_state["running"] = False
    st.session_state["running"] = True

    if st.sidebar.button("Semua Kamera", key="all_cameras", use_container_width=True):
        st.session_state["page"] = "all_cameras"
        st.rerun()  # Stop current loop and rerun to display the selected page

    if st.sidebar.button("Satu Kamera", key="single_camera", use_container_width=True):
        st.session_state["page"] = "single_camera"
        st.rerun()  # Stop current loop and rerun to display the selected page

    if st.sidebar.button("Logout", key="logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["running"] = False  # Stop the loop when logging out
        st.rerun()  # Re-run the app to show the login page

    # Perform initial check for camera availability
    offline_cameras = initial_check(mqtt_receivers)

    # Main content based on the selected page
    if st.session_state["page"] == "all_cameras":
        num_cameras = len(mqtt_receivers)
        num_cols = 2  # Fixed number of columns
        cols = st.columns(num_cols)  # Create two columns

        col_camera_indices = [[] for _ in range(num_cols)]
        i = 0
        for camera_name in mqtt_receivers.keys():
            col_camera_indices[i % num_cols].append(camera_name)
            i += 1

        placeholders = [col.empty() for col in cols for _ in range(len(col_camera_indices[0]))]

        while st.session_state.get("running", False):
            for col_idx, camera_names in enumerate(col_camera_indices):
                for cam_idx, camera_name in enumerate(camera_names):
                    # if camera_name not in offline_cameras:
                        frame = mqtt_receivers[camera_name].get_frame()

                        if frame is not None:
                            placeholders[col_idx * len(col_camera_indices[0]) + cam_idx].image(frame,
                                                                                                caption=camera_name,
                                                                                                use_column_width=True)
                        else:
                            black_image = np.zeros((480, 640, 3), dtype=np.uint8)
                            placeholders[col_idx * len(col_camera_indices[0]) + cam_idx].image(black_image,
                                                                                           caption=f"{camera_name} (No Stream)",
                                                                                           use_column_width=True)

    elif st.session_state["page"] == "single_camera":

        camera_name = st.selectbox("Pilih Kamera", list(mqtt_receivers.keys()))

        placeholders = st.empty()

        while st.session_state.get("running", False):
            frame = mqtt_receivers[camera_name].get_frame()  # Move frame retrieval inside the loop

            if frame is not None:
                placeholders.image(frame, use_column_width=True)
            else:
                black_image = np.zeros((480, 640, 3), dtype=np.uint8)
                placeholders.image(black_image, caption=f"{camera_name} (No Stream)", use_column_width=True)



# --------------------------------------
# Main Application Logic
# --------------------------------------

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def main():
    hide_streamlit_style = """
    <style>
        [data-testid="stHeader"] {
            display: none;
        }
        footer {
            display: none;
        }
        .main {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .streamlit-footer {
            display: none;
        }
    </style>
    """

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "page" not in st.session_state:
        st.session_state["page"] = "all_cameras"

    if "running" not in st.session_state:
        st.session_state["running"] = False

    if st.session_state["authenticated"]:
        camera_streams = load_camera_streams()
        mqtt_receivers = {name: MqttReceiver(topic) for name, topic in camera_streams.items()}

        dashboard(mqtt_receivers)

    else:
        login_page()


if __name__ == "__main__":
    main()
