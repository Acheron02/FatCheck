from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
import shutil

app = FastAPI()

load_dotenv(".env.local")

FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Absolute path to captures folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../captures"))
print(f"[server.py] CAPTURES_DIR set to: {CAPTURES_DIR}", flush=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def find_student_folder(mongo_id: str):
    """
    Recursively find student folder inside:
    captures/grade/section/mongo_id
    """
    if not os.path.exists(CAPTURES_DIR):
        return None

    for grade in os.listdir(CAPTURES_DIR):
        grade_path = os.path.join(CAPTURES_DIR, grade)
        if not os.path.isdir(grade_path):
            continue

        for section in os.listdir(grade_path):
            section_path = os.path.join(grade_path, section)
            if not os.path.isdir(section_path):
                continue

            student_path = os.path.join(section_path, mongo_id)
            if os.path.exists(student_path):
                return student_path

    return None


def get_timestamp_folders(student_folder: str):
    """Return timestamp folders sorted newest to oldest"""
    return sorted(
        [
            d for d in os.listdir(student_folder)
            if os.path.isdir(os.path.join(student_folder, d))
        ],
        reverse=True
    )


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/student/{mongo_id}/records")
def list_student_records(mongo_id: str):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    csv_file = os.path.join(student_folder, "bodyfat_results.csv")
    if not os.path.exists(csv_file):
        raise HTTPException(status_code=404, detail="CSV record not found")

    records = []

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_raw = row.get("Timestamp", "")
            timestamp = timestamp_raw.replace("-", "").replace(":", "").replace(" ", "_")

            pdf_filename = row.get("pdf_filename") or row.get("PDF")
            pdf_url = None

            if pdf_filename:
                pdf_path = os.path.join(student_folder, timestamp, pdf_filename)
                if os.path.exists(pdf_path):
                    pdf_url = f"/student/{mongo_id}/file/{timestamp}/{pdf_filename}"

            records.append({
                "timestamp": timestamp,
                "date": timestamp_raw.split()[0] if timestamp_raw else None,
                "time": timestamp_raw.split()[1] if timestamp_raw else None,
                "body_fat_percent": row.get("Body Fat %") or row.get("body_fat_percent"),
                "category": row.get("Category") or row.get("category"),
                "pdf_url": pdf_url
            })

    return records


@app.get("/student/{mongo_id}/file/{timestamp}/{filename}")
def get_student_file(mongo_id: str, timestamp: str, filename: str):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    full_folder = os.path.join(student_folder, timestamp)
    if not os.path.exists(full_folder):
        raise HTTPException(status_code=404, detail="Capture folder not found")

    file_path = os.path.join(full_folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    return FileResponse(file_path)


@app.get("/student/{mongo_id}/metadata")
def list_student_metadata(mongo_id: str):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    all_metadata = []

    for timestamp_dir in get_timestamp_folders(student_folder):
        full_dir = os.path.join(student_folder, timestamp_dir)

        meta_file = next(
            (f for f in os.listdir(full_dir)
             if f.startswith("metadata_") and f.endswith(".json")),
            None
        )

        if not meta_file:
            continue

        meta_path = os.path.join(full_dir, meta_file)

        try:
            data = json.load(open(meta_path, "r"))
        except Exception as e:
            print(f"[metadata] Failed to read {meta_path}: {e}")
            continue

        data.setdefault("pdf_filename", None)
        data.setdefault("recommended_program", None)
        data.setdefault("body_fat_percent", None)
        data.setdefault("category", None)

        # Convert timestamp_dir to ISO
        try:
            dt = datetime.strptime(timestamp_dir, "%Y%m%d_%H%M%S")
            data["timestamp"] = dt.isoformat()
        except Exception:
            data["timestamp"] = None

        if data["pdf_filename"]:
            pdf_path = os.path.join(full_dir, data["pdf_filename"])
            if os.path.exists(pdf_path):
                data["url"] = f"/student/{mongo_id}/file/{timestamp_dir}/{data['pdf_filename']}"
            else:
                data["url"] = None
        else:
            data["url"] = None

        data["timestamp_dir"] = timestamp_dir
        all_metadata.append(data)

    all_metadata = sorted(
        all_metadata,
        key=lambda x: x["timestamp"] or "",
        reverse=True
    )

    if not all_metadata:
        raise HTTPException(status_code=404, detail="No metadata found")

    return all_metadata


@app.get("/student/{mongo_id}/csv")
def download_student_csv(mongo_id: str):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    csv_file = os.path.join(student_folder, "bodyfat_results.csv")
    if not os.path.exists(csv_file):
        raise HTTPException(status_code=404, detail="CSV file not found")

    return FileResponse(
        csv_file,
        media_type="text/csv",
        filename=f"{mongo_id}_bodyfat_results.csv"
    )


@app.delete("/student/{mongo_id}/metadata/{timestamp}")
def delete_student_record(mongo_id: str, timestamp: str):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    target_folder = os.path.join(student_folder, timestamp)

    if not os.path.exists(target_folder):
        raise HTTPException(status_code=404, detail="Record not found")

    shutil.rmtree(target_folder)

    return {"status": "success", "deleted": timestamp}


@app.delete("/student/{mongo_id}/metadata")
def delete_student_records(
    mongo_id: str,
    all: bool = Query(False),
    timestamps: str = Query(None)
):
    student_folder = find_student_folder(mongo_id)
    if not student_folder:
        raise HTTPException(status_code=404, detail="Student not found")

    deleted = []

    if all:
        for folder in get_timestamp_folders(student_folder):
            shutil.rmtree(os.path.join(student_folder, folder))
            deleted.append(folder)

    elif timestamps:
        ts_list = timestamps.split(",")
        for ts in ts_list:
            folder_path = os.path.join(student_folder, ts)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                deleted.append(ts)
    else:
        raise HTTPException(
            status_code=400,
            detail="No timestamps specified and 'all' not set"
        )

    return {"status": "success", "deleted": deleted}

@app.get("/section/{grade}/{section}/csv")
def download_section_csv(grade: str, section: str):

    section_folder = os.path.join(CAPTURES_DIR, grade, section)

    if not os.path.isdir(section_folder):
        raise HTTPException(status_code=404, detail="Section not found")

    csv_file = os.path.join(section_folder, "section_results.csv")

    if not os.path.isfile(csv_file):
        raise HTTPException(status_code=404, detail="Section CSV not found")

    # ✅ 1. Check file size
    if os.path.getsize(csv_file) == 0:
        raise HTTPException(status_code=404, detail="Section has no records")

    # ✅ 2. Check actual data rows
    try:
        with open(csv_file, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

            # Only header OR empty
            if len(rows) <= 1:
                raise HTTPException(
                    status_code=404,
                    detail="Section has no records"
                )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to validate CSV"
        )

    return FileResponse(
        csv_file,
        media_type="text/csv",
        filename=f"{grade}_{section}_section_results.csv"
    )