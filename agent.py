# agent.py  (robust version using Gemini)
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

from prompts import INTERVIEWER_SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---- Auto-pick a valid model ----
def pick_model():
    """
    Automatically pick a model that:
    - exists in your account
    - supports generateContent
    Preference order: 1.5-flash, 1.5-pro, 1.0-pro, etc.
    """
    preferred = [
        "models/gemini-1.5-flash",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.0-pro",
        "models/gemini-1.0-pro-001",
    ]

    models = list(genai.list_models())
    available = {m.name for m in models if "generateContent" in m.supported_generation_methods}

    for cand in preferred:
        if cand in available:
            return cand

    # Fallback: if nothing matched, just pick the first available generateContent model
    if available:
        return sorted(available)[0]

    raise RuntimeError("No suitable Gemini model with generateContent found. Check your API key and access.")


MODEL_NAME = pick_model()
print(f"[agent.py] Using model: {MODEL_NAME}")


# ---- Core functions ----

def get_next_question(role, interview_type, history, question_number, max_questions):
    """
    history: list of {"question": str, "answer": str}
    Returns: either next_question (str) or "INTERVIEW_COMPLETE"
    """
    system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
        role=role,
        interview_type=interview_type
    )

    user_content = {
        "history": history,
        "question_number": question_number,
        "max_questions": max_questions,
    }

    full_prompt = system_prompt + "\n\nUser Data:\n" + json.dumps(user_content)

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(full_prompt)
    return response.text.strip()


def generate_feedback(role, interview_type, history):
    """
    history: list of {"question": str, "answer": str}
    Returns: dict feedback
    """
    user_content = {
        "role": role,
        "interview_type": interview_type,
        "history": history
    }

    full_prompt = FEEDBACK_SYSTEM_PROMPT + "\n\nUser Data:\n" + json.dumps(user_content)

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(full_prompt)
    raw = response.text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_text": raw}
