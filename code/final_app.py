import streamlit as st
import os
import subprocess
import json
from geopy.distance import geodesic
from streamlit_folium import folium_static
import folium
from patient_summarizer import summarize_patient as summarize_for_doctor
from doctor_recommendor import summarize_patient as summarize_for_patient, load_dataset

# Paths
DOCTOR_OUTPUT_DIR = "../doctor_recommendor"
PATIENT_OUTPUT_DIR = "../summaries"
HOSPITAL_DATA_PATH = "hospital_doctor_data.json"
DATASET_PATH = "../data/Patient_Medical_Records_Dataset_Diverse_Ages.csv"

# Run hospital_locator.py to fetch and display nearest hospital
def run_hospital_locator(user_lat, user_lon, specialist):
    try:
        result = subprocess.run(
            ["python", "hospital_locator.py", str(user_lat), str(user_lon), specialist],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error("Failed to run hospital_locator.py")
        return None

def load_summary(patient_id, output_dir):
    file_path = os.path.join(output_dir, f"{patient_id}_summary.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

st.set_page_config(page_title="Patient Summary & Doctor Recommendation", layout="wide")
st.title("🧪 Patient Summary and Specialist Recommender")

# Load dataset to populate dropdown
patient_data = load_dataset(DATASET_PATH)
all_patient_ids = sorted(patient_data.keys()) if patient_data else []

# Sidebar input
patient_id = st.sidebar.selectbox("Select Patient ID", all_patient_ids)

# Location detection section
with st.sidebar.expander("📍 Location Detection"):
    use_my_location = st.checkbox("Auto Detect My Location")
    if use_my_location:
        st.info("Using default simulated coordinates (e.g., center of Pennsylvania)")
        user_lat, user_lon = 40.2732, -76.8867  # Default fallback
    else:
        user_lat = st.text_input("Latitude", placeholder="e.g., 39.9526")
        user_lon = st.text_input("Longitude", placeholder="e.g., -75.1652")

if st.sidebar.button("Generate Summaries"):
    if not patient_id:
        st.sidebar.warning("Please select a valid Patient ID.")
    else:
        with st.spinner("Generating summaries using LLM..."):
            if patient_id in patient_data:
                summarize_for_doctor(patient_id, patient_data[patient_id])
                summarize_for_patient(patient_id, patient_data[patient_id])
            else:
                st.sidebar.error(f"Patient ID '{patient_id}' not found in the dataset.")

# Layout
col1, col2 = st.columns(2)

# Left: Patient-facing summary
with col1:
    st.header("👤 Patient-Friendly Summary")
    doc_summary = load_summary(patient_id, DOCTOR_OUTPUT_DIR)
    if doc_summary:
        st.text_area("Doctor Summary:", doc_summary, height=400)
    else:
        st.info("Clinical summary not available.")

# Right: Doctor-facing summary and specialist recommendation
with col2:
    st.header("🧪 Doctor-Facing Clinical Summary")
    summary = load_summary(patient_id, PATIENT_OUTPUT_DIR)
    recommended_specialist = None
    if summary:
        st.text_area("Patient Summary:", summary, height=400)
        if "**Recommended Specialist**:" in summary:
            recommended_specialist = summary.split("**Recommended Specialist**:")[-1].strip()
        else:
            for line in summary.splitlines():
                if "Recommended Specialist" in line:
                    recommended_specialist = line.split(":")[-1].strip()
                    break
        if not recommended_specialist and doc_summary:
            if "**Recommended Specialist**:" in doc_summary:
                recommended_specialist = doc_summary.split("**Recommended Specialist**:")[-1].strip()
        if recommended_specialist:
            st.success(f"Recommended Specialist: {recommended_specialist}")
        else:
            st.warning("⚠️ Could not extract specialist type. Check summary formatting.")
            with st.expander("🔍 Show Raw Summary"):
                st.code(summary)
    else:
        st.info("Summary not generated or not found.")

    # Nearest hospital suggestion
    if st.button("Find Nearest Hospital with Specialist"):
        try:
            if isinstance(user_lat, str):
                user_location = (float(user_lat), float(user_lon))
            else:
                user_location = (user_lat, user_lon)

            if recommended_specialist:
                clean_specialist = recommended_specialist.split("(")[0].replace("**", "").strip()
                print(clean_specialist)
                result = run_hospital_locator(user_location[0], user_location[1], clean_specialist)
                if result and 'name' in result:
                    name = result['name']
                    location = result['location']
                    dist = result['distance']
                    st.success(f"Nearest {clean_specialist}: {name} ({dist:.2f} miles away)")

                    hospital_map = folium.Map(location=location, zoom_start=12)
                    folium.Marker(location=location, popup=name, icon=folium.Icon(color='red')).add_to(hospital_map)
                    folium.Marker(location=user_location, popup="You", icon=folium.Icon(color='blue')).add_to(hospital_map)
                    folium_static(hospital_map)
                elif result and 'message' in result:
                    st.error(result['message'])
                elif result and 'error' in result:
                    st.error(result['error'])
                else:
                    st.error("No hospital found with the required specialist.")
            else:
                st.warning("Specialist type not available from summary.")
        except ValueError:
            st.error("Invalid coordinates entered.")
