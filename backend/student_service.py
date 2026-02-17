import requests
import os

BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://192.168.8.196:3000/api/students"
)

def fetch_student_by_id(student_id=None, lrn=None):
    if not student_id and not lrn:
        return None

    # Decide which value to use for API call
    value = student_id or lrn  # fallback to LRN if student_id empty
    try:
        response = requests.get(f"{BASE_URL}/{value}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[fetch_student_by_id] Student not found: {value}")
            return None
    except requests.RequestException as e:
        print("[fetch_student_by_id] API Error:", e)
        return None
