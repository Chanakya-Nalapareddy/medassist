# Medassist


# 🏥 MedAssist - AI-Powered Clinical Summary and Doctor Recommendation System

**Capstone Project – Drexel University | Spring 2025**  
**Team Members:** Chanakya, Uday, Kriti, Neel, Rutvij  

## 💡 Project Overview

**MedAssist** is an AI-driven healthcare assistant designed to improve clinical communication, patient understanding, and decision support. It leverages natural language processing (NLP), large language models (LLMs), and geolocation to:

- Summarize unstructured Electronic Health Records (EHRs)
- Recommend specialists based on extracted medical information
- Identify the nearest suitable hospital based on user location
- Provide patient-friendly and provider-facing summaries
- Offer emergency scheduling, medication reminders, and analytics

## 🚀 Features

| Feature                        | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| 🧾 EHR Summarization           | NLP-based generation of readable summaries for patients and doctors        |
| 👨‍⚕️ Doctor Recommendation     | Suggests appropriate specialists using condition-to-specialist mapping     |
| 🏥 Nearest Hospital Locator    | Geolocation-based filtering of facilities with required specialist         |
| ⏰ Medication Reminders        | Timely alerts based on prescription history and medical restrictions       |
| 📈 Evaluation Metrics          | Supports keyword recall, cosine similarity, BERTScore, etc. (in progress)  |
| 🔐 Secure Backend              | Built with FastAPI and MongoDB with secure endpoints                       |
| 🌐 Frontend Integration        | React UI + interim Streamlit frontend for demo/testing                     |

## 🏗️ Architecture

- **Backend:** FastAPI, MongoDB, Python, OpenRouter API, Google Maps API
- **Frontend:** React.js (main), Streamlit (demo mode), Bootstrap UI components
- **Model:** Microsoft MAI-DS-R1, DeepSeek-V3, OpenRouter LLMs
- **Data:** MT Samples EHR dataset + synthetic hospital metadata

## 📊 Example Case Study

**Patient_2 Summary (Extract):**

- Age 8: Epilepsy diagnosis
- Age 25: Moyamoya disease
- Age 40: Tracheostomy surgery
- Age 70: Valve abnormalities, high pulmonary pressure

🔍 **Recommended Specialist:** Neurologist  
📍 **Nearest Hospital:** Community General Osteopathic Hospital (3.75 miles)

## 📦 Installation & Running the Project

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/medassist.git
cd medassist
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure `.env` file contains your OpenRouter API key:

```env
API_KEY=your_openrouter_api_key
```

### 3. Run Backend (FastAPI)

```bash
uvicorn app.main:app --reload
```

### 4. Run Streamlit Demo Frontend

```bash
streamlit run app/streamlit_frontend.py
```

### 5. (Optional) Run React Frontend

```bash
cd frontend
npm install
npm start
```

## 🧪 Evaluation Metrics (Planned & Implemented)

| Metric              | Use Case                          |
|---------------------|-----------------------------------|
| ✅ Keyword Recall    | Evaluating summarization accuracy |
| ✅ Cosine Similarity | Comparing embedding relevance     |
| 🔄 BERTScore         | Summary quality (planned)         |
| 🔄 SBERT Similarity  | Advanced relevance (planned)      |
| 🔄 Reminder Adherence | Tracking medication alerts        |

## 🔮 Future Enhancements

- Real-time location tracking using Google Places API
- Full React-FastAPI integration replacing interim Streamlit UI
- Multilingual support for broader accessibility
- Voice-based interaction with wearable vitals input
- Appointment scheduling and calendar integration
- Benchmarking with GPT-4o, Gemini, Mistral for robustness

## 📂 Project Structure

```
medassist/
├── code/
|   ├── .env
│   ├── doctor_recommmendor.py                  
│   ├── doctor_recommmendor_app.py/                  
│   ├── final_app/               
│   ├── hospital_doctor_data.json/                 
│   ├── hospital_locator.py/       
│   └── patient_summarizer.py 
├── data/                        
├── doctor_recommendor/                      
├── summaries/                   
├── logs/                        
├── requirements.txt
└── README.md
```

## 👩‍⚕️ References

- [MT Samples Dataset – Kaggle](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions)
- [OpenRouter API](https://openrouter.ai)
- [GeoPy for Distance Calculation](https://geopy.readthedocs.io/en/stable/)
- [OpenStreetMap](https://www.openstreetmap.org)

## 📫 Contact

If you'd like to learn more about MedAssist, contribute, or collaborate on future iterations, feel free to reach out via GitHub Issues or contact the project team!
