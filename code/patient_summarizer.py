import pandas as pd
import requests
import json
import os
import re
import logging
from dotenv import load_dotenv
import argparse


load_dotenv()
api_key = os.getenv("API_KEY")

# Configuration
API_KEY = api_key
API_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = "../summaries"
LOG_DIR = "../logs"
MAX_TOKENS = 10000  # Max input tokens for transcription processing
MODEL = "deepseek/deepseek-chat-v3-0324:free"
# "microsoft/mai-ds-r1:free"

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
    """Load and preprocess the CSV dataset."""
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
    """Truncate text to fit within token limits."""
    max_chars = max_length * 4  # Rough estimate: 1 token ~ 4 characters
    if len(text) > max_chars:
        logging.warning(f"Text truncated from {len(text)} to {max_chars} characters")
        return text[:max_chars] + "... [truncated]"
    return text

def extract_json_from_response(response_text):
    """Extract JSON from response text using regex."""
    json_pattern = r'\{.*?\}'
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def call_openrouter_api(prompt, previous_messages=None, retry=False):
    """Make an API call to OpenRouter."""
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

# def extract_key_information(patient_id, transcriptions, retry_count=0):
#     """Extract structured information from transcriptions."""
#     transcription_text = "\n\n".join(
#         [f"Record {rec['Record_Number']} (Age {rec['Age']}):\n{rec['Transcription']}" 
#          for rec in transcriptions]
#     )
#     transcription_text = truncate_text(transcription_text)
    
#     prompt = f"""
# You are a medical data analyst. Given the medical transcriptions for patient {patient_id}, extract key information in a structured JSON format. Include:
# - Conditions: List of diagnosed diseases/conditions (e.g., ["Asthma", "Obesity"]).
# - Medications: Current and past medications (e.g., ["Albuterol", "Flovent"]).
# - Surgeries: Past surgical procedures (e.g., ["Laparoscopic gastric bypass"]).
# - Allergies: Known allergies (e.g., ["Penicillin"]).
# - Social History: Smoking, alcohol use, marital status, occupation (e.g., {{"smoking": "Nonsmoker", "alcohol": "Rare"}}).
# - Family History: Diseases in family members (e.g., {{"heart_disease": "Grandparents"}}).
# - Key Assessments: Main clinical findings (e.g., ["Wheezing bilaterally"]).
# - Key Plans: Treatments and follow-up plans (e.g., ["Start albuterol inhaler"]).

# **Instructions**:
# - Output **only** a valid JSON object. Do not include any additional text, explanations, or markdown (e.g., ```json).
# - Use null for missing information.
# - Example output:
#   {{
#     "Conditions": ["Asthma"],
#     "Medications": ["Albuterol"],
#     "Surgeries": null,
#     "Allergies": ["Penicillin"],
#     "Social History": {{"smoking": "Nonsmoker", "alcohol": "Minimal"}},
#     "Family History": {{"heart_disease": "Grandparents"}},
#     "Key Assessments": ["Wheezing"],
#     "Key Plans": ["Start Flovent"]
#   }}

# Transcriptions:
# {transcription_text}
# """
#     response = call_openrouter_api(prompt)
#     if not response:
#         return None
    
#     try:
#         structured_data = json.loads(response)
#         logging.info(f"Successfully parsed JSON for {patient_id}")
#         return structured_data
#     except json.JSONDecodeError:
#         logging.warning(f"Failed to parse JSON directly for {patient_id}, attempting extraction")
#         structured_data = extract_json_from_response(response)
#         if structured_data:
#             logging.info(f"Successfully extracted JSON for {patient_id}")
#             return structured_data
        
#         if retry_count < 1:
#             logging.info(f"Retrying extraction for {patient_id}")
#             stricter_prompt = prompt + "\n**Strict Warning**: Output ONLY a valid JSON object with no additional text or formatting. Invalid JSON will be rejected."
#             return extract_key_information(patient_id, transcriptions, retry_count + 1)
        
#         logging.error(f"Failed to parse JSON for {patient_id} after retry")
#         return None

import json
import logging
import re

def extract_key_information(patient_id, transcriptions, retry_count=0):
    """Extract structured information from transcriptions using OpenRouter API."""
    
    transcription_text = "\n\n".join(
        [f"Record {rec['Record_Number']} (Age {rec['Age']}):\n{rec['Transcription']}" 
         for rec in transcriptions]
    )
    transcription_text = truncate_text(transcription_text)

    prompt = f"""
You are a medical data analyst. Given the medical transcriptions for patient {patient_id}, extract key information in a structured JSON format. Include:
- Conditions: List of diagnosed diseases/conditions.
- Medications: Current and past medications.
- Surgeries: Past surgical procedures.
- Allergies: Known allergies.
- Social History: Smoking, alcohol use, marital status, occupation.
- Family History: Diseases in family members.
- Key Assessments: Main clinical findings.
- Key Plans: Treatments and follow-up plans.

**Instructions**:
- Output **only** a valid JSON object. Do not include any explanations or markdown formatting.
- Use `null` for missing information.

Transcriptions:
{transcription_text}
"""

    response = call_openrouter_api(prompt)
    
    if not response:
        logging.error(f"No API response for {patient_id}")
        return None

    # Clean up any markdown formatting like ```json ... ```
    cleaned_response = response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = re.sub(r"```json|```", "", cleaned_response).strip()

    try:
        structured_data = json.loads(cleaned_response)
        logging.info(f"Successfully parsed JSON for {patient_id}")
        return structured_data

    except json.JSONDecodeError:
        logging.warning(f"Direct JSON parsing failed for {patient_id}. Attempting regex extraction.")

        # Try to extract JSON object using regex
        match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
        if match:
            try:
                structured_data = json.loads(match.group(0))
                logging.info(f"Extracted JSON via regex for {patient_id}")
                return structured_data
            except json.JSONDecodeError:
                logging.error(f"Regex-based JSON parsing also failed for {patient_id}")

        if retry_count < 1:
            logging.info(f"Retrying extraction with stricter prompt for {patient_id}")
            stricter_prompt = prompt + "\n\n**STRICT RULE**: Return ONLY a valid JSON object with no formatting, headers, or explanation."
            return extract_key_information(patient_id, transcriptions, retry_count + 1)

        # Final failure
        logging.error(f"Failed to extract JSON for {patient_id} after retry")
        logging.debug(f"Raw API response for {patient_id}:\n{response}")
        return None


# def generate_patient_summary(patient_id, structured_data):
#     """Generate a consistent summary using structured data."""
#     name = f"Patient {patient_id}"

#     # Overview
#     overview = f"{name} is a {structured_data.get('age', 'N/A')}-year-old"
#     if structured_data.get("occupation"):
#         overview += f" {structured_data['occupation']},"
#     if structured_data.get("marital_status"):
#         overview += f" {structured_data['marital_status']},"
#     overview += " with lifestyle history as follows:"
#     smoking = structured_data.get("smoking_status", "N/A")
#     alcohol = structured_data.get("alcohol_use", "N/A")
#     overview += f" Smoking: {smoking}. Alcohol: {alcohol}."

#     # Medical Conditions
#     conditions = structured_data.get("Conditions", [])
#     medical_conditions = "\n- " + "\n- ".join(conditions) if conditions else "\nNone reported."

#     # Surgeries
#     surgeries = structured_data.get("Surgeries", [])
#     surgeries_text = "\n- " + "\n- ".join(surgeries) if surgeries else "\nNo surgical history reported."

#     # Medications & Allergies
#     meds = structured_data.get("Medications", [])
#     allergies = structured_data.get("Allergies", "None reported.")
#     med_text = "\n- " + "\n- ".join(meds) if meds else "\nNone reported."

#     # Social/Family History
#     social = structured_data.get("Social History", "Not provided.")
#     family = structured_data.get("Family History", "Not provided.")

#     # Key Assessments
#     assessments = structured_data.get("Key Assessments", [])
#     diag_text = "\n- " + "\n- ".join(assessments) if assessments else "\nNo assessments noted."

#     # Key Plans
#     plans = structured_data.get("Key Plans", [])
#     plan_text = "\n- " + "\n- ".join(plans) if plans else "\nNo current follow-up plans noted."

#     # Combine everything into a final summary
#     return f"""**Patient Overview**  
# {overview}

# **Medical Conditions**{medical_conditions}

# **Surgeries & Procedures**{surgeries_text}

# **Medications & Allergies**  
# Medications:{med_text}  
# Allergies: {allergies}

# **Social & Family History**  
# Social: {social}  
# Family: {family}

# **Key Assessments & Diagnostics**{diag_text}

# **Management & Follow-up Plans**{plan_text}
# """

def generate_patient_summary(patient_id, structured_data):
    """Generate a consistent summary using structured data."""
    name = f"Patient {patient_id}"

    # Overview
    overview = f"{name} is a {structured_data.get('Age', 'N/A')}-year-old"
    occupation = structured_data.get('SocialHistory', {}).get("Occupation")
    marital = structured_data.get('SocialHistory', {}).get("MaritalStatus")
    if occupation:
        overview += f" {occupation},"
    if marital:
        overview += f" {marital},"
    overview += " with lifestyle history as follows:"
    smoking = structured_data.get('SocialHistory', {}).get("Smoking", "N/A")
    alcohol = structured_data.get('SocialHistory', {}).get("Alcohol", "N/A")
    overview += f" Smoking: {smoking}. Alcohol: {alcohol}."

    # Medical Conditions
    conditions = structured_data.get("Condition", [])
    medical_conditions = "\n- " + "\n- ".join(conditions) if conditions else "\nNone reported."

    # Surgeries
    surgeries = structured_data.get("Surgery", [])
    surgeries_text = "\n- " + "\n- ".join(surgeries) if surgeries else "\nNo surgical history reported."

    # Medications & Allergies
    meds = structured_data.get("Medication", [])
    med_text = "\n- " + "\n- ".join(meds) if meds else "\nNone reported."
    allergies = structured_data.get("Allergy", "None reported.") or "None reported."

    # Social/Family History
    social = json.dumps(structured_data.get("SocialHistory", "Not provided."), indent=2)
    family = structured_data.get("FamilyHistory", "Not provided.")

    # Key Assessments
    assessments = structured_data.get("KeyAssessment", [])
    diag_text = "\n- " + "\n- ".join(assessments) if assessments else "\nNo assessments noted."

    # Key Plans
    plans = structured_data.get("KeyPlan", [])
    plan_text = "\n- " + "\n- ".join(plans) if plans else "\nNo current follow-up plans noted."

    # Combine everything into a final summary
    return f"""**Patient Overview**  
{overview}

**Medical Conditions**{medical_conditions}

**Surgeries & Procedures**{surgeries_text}

**Medications & Allergies**  
Medications:{med_text}  
Allergies: {allergies}

**Social & Family History**  
Social: {social}  
Family: {family}

**Key Assessments & Diagnostics**{diag_text}

**Management & Follow-up Plans**{plan_text}
"""


def generate_draft_summary(patient_id, structured_data):
    """Generate the draft summary based on structured data."""
    draft_summary = generate_patient_summary(patient_id, structured_data)
    
    # Ensure the summary is concise but professional, while adhering to the format
    summary_lines = draft_summary.split("\n")
    concise_summary = "\n".join(summary_lines[:25])  # Limit to 25 lines as a rough word count control
    
    logging.info(f"Draft summary generated for {patient_id}")
    return concise_summary

# def refine_summary(patient_id, draft_summary):
#     """Prompt 3: Refine the draft summary."""
# #     prompt = f"""
# # You are a medical editor. Refine the following draft summary for patient {patient_id} to make it clear, concise, and professional. Ensure:
# # - All medical history is included (conditions, treatments, surgeries, medications, allergies, social/family history).
# # - The summary is 150-200 words.
# # - Use medical terminology appropriately, but keep it readable for healthcare professionals.
# # - Organize chronologically and highlight key transitions in health.

# # Draft Summary:
# # {draft_summary}

# # Output the final summary in plain text.
# # """
#     prompt = f"""
# You are a medical writer. Convert the following draft summary for patient {patient_id} into a professionally structured medical summary with the following section headers:

# *Early Childhood*  
# *Adolescence*  
# *Adulthood*  
# *Recent Hospitalization (if any)*  
# *Current Medications*  
# *Allergies*  
# *Social History*  
# *Family History*  
# *Follow-Up*  
# *Summary*

# Instructions:
# - Use bullet points only where medically appropriate.
# - Be concise but include all relevant history.
# - Write in plain, readable clinical language.
# - If a section is not applicable, omit it.
# - Final output should be formatted in plain text, no markdown or JSON.

# Draft Summary:
# {draft_summary}
# """

#     response = call_openrouter_api(prompt)
#     if response:
#         logging.info(f"Final summary refined for {patient_id}")
#     return response

def refine_summary(patient_id, draft_summary, structured_data):
    """Prompt 3: Refine the draft summary with structured data for accuracy."""

    # Handle medications
    medications = structured_data.get('Medications', [])
    medication_names = [
        m['name'] if isinstance(m, dict) and 'name' in m else str(m) 
        for m in medications
    ]
    medication_table = "\n".join([
        f"| {m.get('name', '')} | {m.get('Dosage', '')} | {m.get('Age', '')} |"
        for m in medications if isinstance(m, dict)
    ])

    # Handle surgeries
    surgeries = structured_data.get('Surgeries', [])
    surgery_names = [
        s['name'] if isinstance(s, dict) and 'name' in s else str(s)
        for s in surgeries or []
    ]

    # Key assessments
    assessments = structured_data.get('Key Assessments', [])
    assessment_texts = [
        f"**Age {a.get('Age', '?')}:** {a.get('Findings', '')}"
        for a in assessments if isinstance(a, dict)
    ]

    # Key plans
    plans = structured_data.get('Key Plans', [])
    plan_texts = [
        f"**Age {p.get('Age', '?')}:** {p.get('Plan', 'N/A')}"
        for p in plans if isinstance(p, dict)
    ]

    # Social history
    social_list = structured_data.get('Social History', [])
    social_lines = []
    for s in social_list:
        if isinstance(s, dict):
            desc = ", ".join([
                f"{k}: {v}" for k, v in s.items() if v is not None
            ])
            social_lines.append(f"- Age {s.get('Age', '?')}: {desc}")

    # Family history
    family_hist = structured_data.get("Family History", [])
    family_lines = []
    for f in family_hist:
        if isinstance(f, dict):
            family_lines.append(f"- {f.get('Relation', 'Unknown')}: {f.get('Condition', '')}")

    # Markdown-formatted structured data
    structured_data_summary = f"""
### 🧍‍♀️ Patient Overview
- **Patient ID:** {patient_id}

### 🩺 Medical Conditions
{', '.join(structured_data.get('Conditions', [])) or 'None'}

### 💊 Medications
| Name | Dosage | Age Started |
|------|--------|-------------|
{medication_table or 'None'}

### 🏥 Surgeries
{', '.join(surgery_names) or 'None'}

### ⚠️ Allergies
{structured_data.get('Allergies', 'None') or 'None'}

### 👪 Social History
{chr(10).join(social_lines) or 'Not provided.'}

### 🧬 Family History
{chr(10).join(family_lines) or 'Not provided.'}

### 🔍 Key Assessments
{chr(10).join(assessment_texts) or 'None'}

### 📝 Key Plans
{chr(10).join(plan_texts) or 'None'}
"""
    return structured_data_summary


    prompt = f"""
You are a medical writer tasked with refining a draft summary for patient {patient_id} into a professionally structured medical summary. Use the provided draft summary and structured data to ensure accuracy. Organize the summary with the following section headers, omitting any section with no relevant data:

- Early Childhood
- Adolescence
- Adulthood
- Recent Hospitalization
- Current Medications
- Allergies
- Social History
- Family History
- Key Assessments
- Key Plans
- Summary

**Instructions**:
- Use the draft summary and structured data to populate each section accurately.
- If no data exists for a section (e.g., Early Childhood), omit it entirely.
- Write in concise, clinical language suitable for healthcare professionals.
- Use bullet points only for lists (e.g., medications, conditions).
- Ensure the summary is 150-200 words, prioritizing key medical details.
- Output in plain text, with section headers in title case (e.g., Current Medications).
- Do not include markdown, JSON, or extraneous text.

Draft Summary:
{draft_summary}

{structured_data_summary}
"""

    # Truncate prompt if necessary to avoid API token limits
    prompt = truncate_text(prompt, max_length=3000)  # Adjust to fit within API limits

    response = call_openrouter_api(prompt)
    if response:
        logging.info(f"Final summary refined for {patient_id}")
        # Clean up any unexpected markdown or formatting
        response = re.sub(r"```[\s\S]*?```", "", response).strip()
        return response
    else:
        logging.error(f"Failed to refine summary for {patient_id}: No API response")
        print(f"Failed to refine summary for {patient_id}: No API response")
        return None

def save_summary(patient_id, summary):
    """Save the summary to a file."""
    file_path = os.path.join(OUTPUT_DIR, f"{patient_id}_summary.txt")
    try:
        with open(file_path, 'w') as f:
            f.write(summary)
        logging.info(f"Summary saved for {patient_id} at {file_path}")
        print(f"Summary saved for {patient_id} at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save summary for {patient_id}: {e}")
        print(f"Failed to save summary for {patient_id}: {e}")

# def summarize_patient(patient_id, patient_data):
#     """Process a single patient's data through prompt chaining."""
#     print(f"Processing patient {patient_id}...")
#     logging.info(f"Starting processing for {patient_id}")
    
#     # Step 1: Extract key information
#     structured_data = extract_key_information(patient_id, patient_data['transcriptions'])
#     if not structured_data:
#         print(f"Failed to extract structured data for {patient_id}")
#         logging.error(f"Failed to extract structured data for {patient_id}")
#         return
    
#     # Step 2: Generate draft summary using the consistent format
#     draft_summary = generate_draft_summary(patient_id, structured_data)
#     if not draft_summary:
#         print(f"Failed to generate draft summary for {patient_id}")
#         logging.error(f"Failed to generate draft summary for {patient_id}")
#         return
    
#     # Step 3: Refine summary (if necessary, refining can still be done as per your original code)
#     final_summary = refine_summary(patient_id, draft_summary)
#     if not final_summary:
#         print(f"Failed to refine summary for {patient_id}")
#         logging.error(f"Failed to refine summary for {patient_id}")
#         return
    
#     # Save the final summary
#     save_summary(patient_id, final_summary)

def summarize_patient(patient_id, patient_data):
    """Process a single patient's data through prompt chaining."""
    print(f"Processing patient {patient_id}...")
    logging.info(f"Starting processing for {patient_id}")
    
    # Step 1: Extract key information
    structured_data = extract_key_information(patient_id, patient_data['transcriptions'])
    if not structured_data:
        print(f"Failed to extract structured data for {patient_id}")
        logging.error(f"Failed to extract structured data for {patient_id}")
        return
    
    # Step 2: Generate draft summary
    draft_summary = generate_draft_summary(patient_id, structured_data)
    if not draft_summary:
        print(f"Failed to generate draft summary for {patient_id}")
        logging.error(f"Failed to generate draft summary for {patient_id}")
        return
    logging.debug(f"Draft summary for {patient_id}:\n{draft_summary}")
    
    # Step 3: Refine summary
    final_summary = refine_summary(patient_id, draft_summary, structured_data)
    if not final_summary:
        print(f"Failed to refine summary for {patient_id}")
        logging.error(f"Failed to refine summary for {patient_id}")
        return
    
    # Save the final summary
    save_summary(patient_id, final_summary)

def main():
    """Main function to process the dataset and generate summaries."""
    parser = argparse.ArgumentParser(description="Generate summary for a specific patient.")
    parser.add_argument("--patient_id", type=str, required=True, help="Patient ID to summarize")

    args = parser.parse_args()
    selected_patient_id = args.patient_id

    file_path = "../data/Patient_Medical_Records_Dataset_Diverse_Ages.csv"
    patient_data = load_dataset(file_path)

    if not patient_data:
        print("Exiting due to dataset loading failure.")
        logging.error("Exiting due to dataset loading failure")
        return

    if selected_patient_id in patient_data:
        summarize_patient(selected_patient_id, patient_data[selected_patient_id])
    else:
        print(f"Patient ID '{selected_patient_id}' not found in the dataset.")
        logging.warning(f"Patient ID '{selected_patient_id}' not found in dataset")


if __name__ == "__main__":
    main()
