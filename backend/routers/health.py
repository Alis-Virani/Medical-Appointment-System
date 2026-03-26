"""Health history router."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, UploadFile, File
from backend.auth_utils import get_current_user
from database import DB_NAME
import sqlite3

router = APIRouter()


@router.get("/history")
def health_history(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        SELECT symptom, condition, specialist, recorded_at
        FROM patient_memory
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 50
    """, (current_user["id"],))
    rows = cur.fetchall()
    conn.close()
    return [
        {"symptom": r[0], "condition": r[1], "specialist": r[2], "recorded_at": r[3]}
        for r in rows
    ]


@router.delete("/history")
def clear_health_history(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("DELETE FROM patient_memory WHERE user_id = ?", (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "Symptom history cleared"}


@router.post("/report")
async def analyze_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze a medical report image."""
    try:
        content = await file.read()
        # Save temp file
        import tempfile
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        from report_analyzer import analyze_medical_report
        result = analyze_medical_report(tmp_path)
        os.unlink(tmp_path)
        return {"analysis": result, "filename": file.filename}
    except Exception as e:
        return {"analysis": f"Could not analyze report: {str(e)}", "filename": file.filename}
