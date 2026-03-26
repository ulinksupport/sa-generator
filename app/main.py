# main.py

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from docx_generator import generate_docx
from knowledge_loader import load_knowledge
from openai_service import run_document_driven_intake
from placeholder_mapper import build_placeholder_mapping

app = FastAPI(title="BD Service Agreement Generator")

knowledge_base = load_knowledge()


class ChatRequest(BaseModel):
    message: str
    known_answers: dict[str, Any] = Field(default_factory=dict)
    source_documents: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    assistant_reply: str
    answers: dict[str, Any]
    extracted_fields: dict[str, Any]
    missing_items: list[str]
    next_question: str
    next_options: list[str]
    is_complete: bool


class GenerateRequest(BaseModel):
    answers: dict[str, Any]
    template_path: str
    output_path: str


class GenerateResponse(BaseModel):
    status: str
    output_path: str
    placeholder_mapping: dict[str, str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    source_docs = req.source_documents if req.source_documents is not None else knowledge_base

    result = run_document_driven_intake(
        source_documents=source_docs,
        known_answers=req.known_answers,
        user_message=req.message,
    )

    updated_answers = {**req.known_answers, **result.get("extracted_fields", {})}

    return ChatResponse(
        assistant_reply=result.get("assistant_reply", ""),
        answers=updated_answers,
        extracted_fields=result.get("extracted_fields", {}),
        missing_items=result.get("missing_items", []),
        next_question=result.get("next_question", ""),
        next_options=result.get("next_options", []),
        is_complete=bool(result.get("is_complete", False)),
    )


@app.post("/generate-doc", response_model=GenerateResponse)
def generate_document(req: GenerateRequest) -> GenerateResponse:
    template_path = Path(req.template_path)
    if not template_path.exists():
        raise HTTPException(status_code=400, detail="Template file not found")

    output_path = Path(req.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mapping = build_placeholder_mapping(req.answers)
    final_path = generate_docx(
        template_path=str(template_path),
        output_path=str(output_path),
        placeholder_mapping=mapping,
    )

    return GenerateResponse(
        status="success",
        output_path=final_path,
        placeholder_mapping=mapping,
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)