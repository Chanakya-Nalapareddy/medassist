import streamlit as st
import os
import subprocess
from patient_summarizer import summarize_patient as summarize_for_doctor
from doctor_recommendor import summarize_patient as summarize_for_patient, load_dataset

# Paths
DOCTOR_OUTPUT_DIR = "../doctor_recommendor"
PATIENT_OUTPUT_DIR = "../summaries"
DATASET_PATH = "../data/Patient_Medical_Records_Dataset_Diverse_Ages.csv"

def load_summary(patient_id, output_dir):
    file_path = os.path.join(output_dir, f"{patient_id}_summary.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

st.set_page_config(page_title="Patient Summary & Doctor Recommendation", layout="wide")
st.title("🩺 Patient Summary and Specialist Recommender")

# Load dataset to populate dropdown
patient_data = load_dataset(DATASET_PATH)
all_patient_ids = sorted(patient_data.keys()) if patient_data else []

# Sidebar input
patient_id = st.sidebar.selectbox("Select Patient ID", all_patient_ids)

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

# Right: Doctor-facing summary
with col2:
    st.header("🩺 Doctor-Facing Clinical Summary")
    summary = load_summary(patient_id, PATIENT_OUTPUT_DIR)
    if summary:
        st.text_area("Patient Summary:", summary, height=400)
        if "**Recommended Specialist**:" in summary:
            specialist = summary.split("**Recommended Specialist**:")[-1].strip()
            st.success(f"Recommended Specialist: {specialist}")
    else:
        st.info("Summary not generated or not found.")
    
