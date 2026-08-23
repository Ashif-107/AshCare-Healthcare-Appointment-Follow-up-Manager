import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# We use placeholders for API keys.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "mock_key")

def get_groq_client():
    if GROQ_API_KEY == "mock_key":
        return None
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Error initializing Groq: {e}")
        return None

def generate_pre_visit_summary(symptoms: str) -> dict:
    client = get_groq_client()
    if not client:
        return {
            "urgency_level": "Medium",
            "chief_complaint": "General consultation",
            "suggested_questions": "1. What is the cause?\n2. What are the treatment options?\n3. When should I follow up?",
            "full_summary": "[MOCK] AI Pre-visit Summary: The patient reported: " + symptoms
        }
    
    prompt = f"Analyse these symptoms and return: urgency level (Low / Medium / High), chief complaint, and three suggested questions for the doctor to ask the patient during the consultation. Format as a clinical pre-visit brief. Symptoms: {symptoms}"
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="openai/gpt-oss-20b",
        )
        response_text = chat_completion.choices[0].message.content
        
        # Simple parsing logic for the sake of the challenge
        urgency = "Medium"
        if "High" in response_text: urgency = "High"
        elif "Low" in response_text: urgency = "Low"
        
        return {
            "urgency_level": urgency,
            "chief_complaint": "Extracted from AI",
            "suggested_questions": "1. 2. 3.",
            "full_summary": response_text
        }
    except Exception as e:
        print(f"LLM Failure: {e}")
        return {
            "urgency_level": "Medium",
            "chief_complaint": "Error parsing",
            "suggested_questions": "Could not generate questions.",
            "full_summary": f"Failed to generate summary due to API error."
        }

def generate_post_visit_summary(notes: str) -> str:
    client = get_groq_client()
    if not client:
        return "[MOCK] Patient-friendly summary: Please take your prescribed medicines and rest well. Notes: " + notes
    
    prompt = f"Convert these clinical notes into a patient-friendly summary with medication schedule and follow-up steps: {notes}"
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="openai/gpt-oss-20b",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"LLM Failure: {e}")
        return "Failed to generate patient-friendly summary due to API error."
