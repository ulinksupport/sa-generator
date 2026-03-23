from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Matter, Message, MatterAnswer
from .knowledge_loader import load_source_documents
from .openai_service import run_document_driven_intake

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message": "BD Service Agreement Generator is running"
    }

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
      <head>
        <title>BD Service Agreement Generator</title>
      </head>
      <body>
        <h1>BD Service Agreement Generator</h1>
        <p>Your Render site is working.</p>
      </body>
    </html>
    """
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    extracted_fields: dict
    missing_items: list[str]
    next_question: str | None
    next_options: list[str]
    is_complete: bool

def upsert_answer(db: Session, matter_id: int, field_key: str, field_value: str):
    existing = (
        db.query(MatterAnswer)
        .filter(
            MatterAnswer.matter_id == matter_id,
            MatterAnswer.field_key == field_key
        )
        .first()
    )

    if existing:
        existing.field_value = field_value
    else:
        db.add(
            MatterAnswer(
                matter_id=matter_id,
                field_key=field_key,
                field_value=field_value
            )
        )


def get_answer_map(db: Session, matter_id: int) -> dict:
    answers = db.query(MatterAnswer).filter(MatterAnswer.matter_id == matter_id).all()
    return {a.field_key: a.field_value for a in answers}

@app.post("/matters/{matter_id}/chat", response_model=ChatResponse)
def chat_with_matter(matter_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # Save user's message
    db.add(
        Message(
            matter_id=matter_id,
            sender_name="User",
            role="user",
            content=payload.message
        )
    )
    db.commit()

    # Load current answers + source docs
    known_answers = get_answer_map(db, matter_id)
    source_documents = load_source_documents()

    # Ask OpenAI to drive intake from docs
    result = run_document_driven_intake(
        source_documents=source_documents,
        known_answers=known_answers,
        user_message=payload.message
    )

    extracted_fields = result.get("extracted_fields", {})
    saved_fields = {}

    for key, value in extracted_fields.items():
        if value is not None and str(value).strip():
            clean_value = str(value).strip()
            upsert_answer(db, matter_id, key, clean_value)
            saved_fields[key] = clean_value

    db.commit()

    assistant_reply = result.get("assistant_reply", "Okay.")
    missing_items = result.get("missing_items", [])
    next_question = result.get("next_question")
    next_options = result.get("next_options", [])
    is_complete = bool(result.get("is_complete", False))

    # Save assistant message
    db.add(
        Message(
            matter_id=matter_id,
            sender_name="Assistant",
            role="assistant",
            content=assistant_reply
        )
    )
    db.commit()

    return ChatResponse(
        reply=assistant_reply,
        extracted_fields=saved_fields,
        missing_items=missing_items,
        next_question=next_question,
        next_options=next_options,
        is_complete=is_complete
    )

@app.get("/matters/{matter_id}/start", response_model=ChatResponse)
def start_matter_intake(matter_id: int, db: Session = Depends(get_db)):
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    known_answers = get_answer_map(db, matter_id)
    source_documents = load_source_documents()

    result = run_document_driven_intake(
        source_documents=source_documents,
        known_answers=known_answers,
        user_message="Start the intake and ask the first question."
    )

    assistant_reply = result.get("assistant_reply", "Let's begin.")
    missing_items = result.get("missing_items", [])
    next_question = result.get("next_question")
    next_options = result.get("next_options", [])
    is_complete = bool(result.get("is_complete", False))

    db.add(
        Message(
            matter_id=matter_id,
            sender_name="Assistant",
            role="assistant",
            content=assistant_reply
        )
    )
    db.commit()

    return ChatResponse(
        reply=assistant_reply,
        extracted_fields={},
        missing_items=missing_items,
        next_question=next_question,
        next_options=next_options,
        is_complete=is_complete
    )

@app.get("/health")
def health():
    return {"status": "ok"}