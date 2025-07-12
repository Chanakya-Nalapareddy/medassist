import os
import re
import json
import argparse
import logging
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = "../doctor_recommendor"
LOG_DIR = "../logs"
MAX_TOKENS = 10000
MODEL = "deepseek/deepseek-chat-v3-0324:free"

# Ensure output and log directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "summarizer.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
        patient_data = df.groupby('Patient_ID').apply(
            lambda x: {
                'transcriptions': x[['Record_Number', 'Transcription', 'Age']].to_dict('records'),
                'records': x.to_dict('records')
            }
        ).to_dict()
        logging.info(f"Dataset loaded successfully from {file_path}")
        return patient_data
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        print(f"Failed to load dataset: {e}")
        return None

def truncate_text(text, max_length=MAX_TOKENS):
    max_chars = max_length * 4  # Approximate token to character ratio
    if len(text) > max_chars:
        logging.warning(f"Text truncated from {len(text)} to {max_chars} characters")
        return text[:max_chars] + "... [truncated]"
    return text

def call_openrouter_api(prompt, previous_messages=None, retry=False):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = previous_messages or []
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_text = response.json()['choices'][0]['message']['content']
        logging.debug(f"API response: {response_text}")
        return response_text
    except Exception as e:
        logging.error(f"API call failed: {e}")
        print(f"API call failed: {e}")
        return None

def extract_patient_summary(patient_id, transcriptions):
    transcription_text = "\n\n".join(
        [f"Record {rec['Record_Number']} (Age {rec['Age']}):\n{rec['Transcription']}" 
         for rec in transcriptions]
    )
    transcription_text = truncate_text(transcription_text)

    prompt = f"""
You are a healthcare assistant. Your task is to help patient {patient_id} understand their medical history based on the following transcriptions from various medical visits.

Please do the following:
- Summarize the patient's medical history in simple, easy-to-understand language suitable for a non-medical audience.
- Clearly highlight important diagnoses, treatments, medications, allergies, surgeries, and relevant lifestyle details.
- Organize the information chronologically to help the patient follow their health journey.
- Keep the summary concise but comprehensive.

At the end, on a separate line, provide the most relevant type of medical specialist the patient should consider visiting. Format it like this:
**Recommended Specialist**: [name of the specialist]

Transcriptions:
{transcription_text}

Output only the final summary in plain text, followed by the recommended specialist on a new line.
"""
    response = call_openrouter_api(prompt)
    if not response:
        logging.error(f"No API response for {patient_id}")
        return None
    logging.info(f"Received summary response for {patient_id}")
    return response.strip()

def save_summary(patient_id, summary):
    file_path = os.path.join(OUTPUT_DIR, f"{patient_id}_summary.txt")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        logging.info(f"Summary saved for {patient_id} at {file_path}")
        print(f"Summary saved for {patient_id} at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save summary for {patient_id}: {e}")
        print(f"Failed to save summary for {patient_id}: {e}")

def summarize_patient(patient_id, patient_data):
    print(f"Processing patient {patient_id}...")
    logging.info(f"Starting processing for {patient_id}")

    summary = extract_patient_summary(patient_id, patient_data['transcriptions'])
    if not summary:
        print(f"Failed to generate summary for {patient_id}")
        logging.error(f"Failed to generate summary for {patient_id}")
        return

    save_summary(patient_id, summary)

def main():
    parser = argparse.ArgumentParser(description="Generate summary for a specific patient.")
    parser.add_argument("--patient_id", type=str, required=True, help="Patient ID to summarize")
    args = parser.parse_args()
    selected_patient_id = args.patient_id

    file_path = "../data/Patient_Medical_Records_Dataset_Diverse_Ages.csv"
    patient_data = load_dataset(file_path)
    if not patient_data:
        print("Exiting due to dataset loading failure.")
        return

    if selected_patient_id in patient_data:
        summarize_patient(selected_patient_id, patient_data[selected_patient_id])
    else:
        print(f"Patient ID '{selected_patient_id}' not found in the dataset.")
        logging.warning(f"Patient ID '{selected_patient_id}' not found in dataset")

if __name__ == "__main__":
    main()
