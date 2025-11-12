import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from database import db, create_document, get_documents
from schemas import DASSAssessment, DASSResult

app = FastAPI(title="DASS-21 Mental Health API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "DASS-21 Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# DASS-21 scoring configuration
# Items are indexed 1..21 in the published scale; our answers array is 0..20
DEPRESSION_IDX = [3, 5, 10, 13, 16, 17, 21]       # 3,5,10,13,16,17,21
ANXIETY_IDX    = [2, 4, 7, 9, 15, 19, 20]         # 2,4,7,9,15,19,20
STRESS_IDX     = [1, 6, 8, 11, 12, 14, 18]        # 1,6,8,11,12,14,18

# Convert 1-based to 0-based indices
DEP_I = [i-1 for i in DEPRESSION_IDX]
ANX_I = [i-1 for i in ANXIETY_IDX]
STR_I = [i-1 for i in STRESS_IDX]

# Severity thresholds for DASS-21 (sum of 7 items, no doubling)
DEP_THRESH = [(0,4,'Normal'), (5,6,'Mild'), (7,10,'Moderate'), (11,13,'Severe'), (14,42,'Extremely Severe')]
ANX_THRESH = [(0,3,'Normal'), (4,5,'Mild'), (6,7,'Moderate'), (8,9,'Severe'), (10,42,'Extremely Severe')]
STR_THRESH = [(0,7,'Normal'), (8,9,'Mild'), (10,12,'Moderate'), (13,16,'Severe'), (17,42,'Extremely Severe')]


def severity_for(score: int, bands: List[tuple]) -> str:
    for lo, hi, label in bands:
        if lo <= score <= hi:
            return label
    return bands[-1][2]


class ScoreResponse(DASSResult):
    pass

@app.post("/api/score", response_model=ScoreResponse)
def score_dass(assessment: DASSAssessment) -> DASSResult:
    answers = assessment.answers
    if len(answers) != 21 or any(a not in (0,1,2,3) for a in answers):
        raise HTTPException(status_code=400, detail="answers must be 21 integers each 0-3")

    dep = sum(answers[i] for i in DEP_I)
    anx = sum(answers[i] for i in ANX_I)
    stress = sum(answers[i] for i in STR_I)

    result = DASSResult(
        depression_score=dep,
        anxiety_score=anx,
        stress_score=stress,
        depression_severity=severity_for(dep, DEP_THRESH),
        anxiety_severity=severity_for(anx, ANX_THRESH),
        stress_severity=severity_for(stress, STR_THRESH),
        total_score=sum(answers)
    )

    # Persist to DB if available
    try:
        doc = assessment.model_dump()
        doc.update({
            "depression_score": dep,
            "anxiety_score": anx,
            "stress_score": stress,
            "depression_severity": result.depression_severity,
            "anxiety_severity": result.anxiety_severity,
            "stress_severity": result.stress_severity,
            "total_score": result.total_score,
        })
        inserted_id = create_document("dassassessment", doc)
        result.assessment_id = inserted_id
    except Exception:
        # If DB not configured, just skip persistence
        pass

    return result

@app.get("/api/assessments")
def list_assessments(limit: int = 20) -> List[Dict[str, Any]]:
    try:
        docs = get_documents("dassassessment", limit=limit)
        # Convert ObjectId to string
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"]) 
        return docs
    except Exception:
        # If DB not configured
        return []


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
