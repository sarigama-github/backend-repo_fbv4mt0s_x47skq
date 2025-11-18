import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Study App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert ObjectId to string recursively

def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"]) 
    return doc

# Models for simple creates (frontend will call these)
class CreateTopic(BaseModel):
    name: str
    description: Optional[str] = None

class CreateCard(BaseModel):
    topic_id: str
    question: str
    answer: str
    difficulty: Optional[str] = "medium"

class AnswerPayload(BaseModel):
    card_id: str
    topic_id: str
    correct: bool

@app.get("/")
async def root():
    return {"message": "Study App Backend Running"}

@app.get("/schema")
async def get_schema():
    # Let the platform read available schemas
    try:
        import schemas
        # Expose model names list
        return {"models": [name for name in dir(schemas) if name[0].isupper()]}
    except Exception as e:
        return {"error": str(e)}

# Topics
@app.post("/api/topics")
async def create_topic(payload: CreateTopic):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    topic_id = create_document("topic", payload.model_dump())
    return {"id": topic_id}

@app.get("/api/topics")
async def list_topics():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    items = [serialize_doc(d) for d in get_documents("topic", {})]
    return items

# Cards
@app.post("/api/cards")
async def create_card(payload: CreateCard):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Basic validation topic exists
    topic = db["topic"].find_one({"_id": ObjectId(payload.topic_id)})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    card_id = create_document("card", payload.model_dump())
    return {"id": card_id}

@app.get("/api/cards")
async def list_cards(topic_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    query = {"topic_id": topic_id} if topic_id else {}
    items = [serialize_doc(d) for d in get_documents("card", query)]
    return items

# Study session endpoints
@app.post("/api/answer")
async def submit_answer(payload: AnswerPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Ensure card exists
    try:
        card = db["card"].find_one({"_id": ObjectId(payload.card_id)})
    except Exception:
        card = None
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    log_id = create_document("studylog", payload.model_dump())
    return {"id": log_id}

@app.get("/api/progress")
async def get_progress(topic_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    query = {"topic_id": topic_id} if topic_id else {}
    logs = list(db["studylog"].find(query))
    total = len(logs)
    correct = sum(1 for l in logs if l.get("correct"))
    return {"total": total, "correct": correct, "accuracy": (correct/total if total else 0)}

@app.get("/test")
async def test_database():
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
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
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
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
