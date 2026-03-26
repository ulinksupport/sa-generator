from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Client, Matter, Message, MatterAnswer
from .knowledge_loader import load_source_documents
from .openai_service import run_document_driven_intake

from datetime import datetime
from sqlalchemy.exc import IntegrityError

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
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BD Service Agreement Generator</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f5f7fb;
      color: #1f2937;
    }
    .app {
      display: grid;
      grid-template-columns: 260px 1fr 320px;
      height: 100vh;
    }
    .sidebar, .rightbar {
      background: #ffffff;
      border-right: 1px solid #e5e7eb;
      padding: 16px;
      overflow-y: auto;
    }
    .rightbar {
      border-right: none;
      border-left: 1px solid #e5e7eb;
    }
    .main {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .topbar {
      background: #ffffff;
      border-bottom: 1px solid #e5e7eb;
      padding: 12px 16px;
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
    }
    .chat-wrap {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }
    .composer {
      background: #ffffff;
      border-top: 1px solid #e5e7eb;
      padding: 12px 16px;
      display: flex;
      gap: 8px;
    }
    textarea {
      flex: 1;
      min-height: 70px;
      resize: vertical;
      padding: 10px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font: inherit;
    }
    button {
      border: none;
      border-radius: 8px;
      padding: 10px 14px;
      background: #2563eb;
      color: white;
      cursor: pointer;
      font-weight: 600;
    }
    button.secondary {
      background: #e5e7eb;
      color: #111827;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .card {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 12px;
    }
    .message {
      max-width: 80%;
      padding: 12px;
      border-radius: 12px;
      margin-bottom: 10px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .user {
      margin-left: auto;
      background: #dbeafe;
    }
    .assistant {
      margin-right: auto;
      background: #ffffff;
      border: 1px solid #e5e7eb;
    }
    .label {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .value {
      font-size: 14px;
      word-break: break-word;
    }
    .small {
      font-size: 13px;
      color: #4b5563;
    }
    .status {
      font-size: 14px;
      color: #374151;
    }
    .matter-id {
      font-weight: 700;
      color: #2563eb;
    }
    .hint {
      font-size: 13px;
      color: #6b7280;
      margin-top: 8px;
    }
    ul {
      padding-left: 18px;
      margin: 6px 0 0;
    }
    .row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .pill {
      display: inline-block;
      background: #eef2ff;
      color: #3730a3;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      margin: 4px 6px 0 0;
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <h2 style="margin-top:0;">BD Tool</h2>

      <div class="card">
        <div class="label">Matter Controls</div>
        <div class="row">
          <button id="createMatterBtn">Create test matter</button>
          <button id="startBtn" class="secondary" disabled>Start intake</button>
        </div>
        <div class="hint">Use Create test matter first, then Start intake.</div>
      </div>

      <div class="card">
        <div class="label">Current Matter</div>
        <div class="value">Matter ID: <span id="matterId" class="matter-id">None</span></div>
        <div class="value">Client ID: <span id="clientId">None</span></div>
      </div>

      <div class="card">
        <div class="label">Last Assistant Guidance</div>
        <div id="nextQuestion" class="value">No question yet.</div>
        <div id="nextOptions" class="small"></div>
      </div>
    </aside>

    <main class="main">
      <div class="topbar">
        <div>
          <strong>Shared Chat</strong>
          <div class="status" id="statusText">Ready.</div>
        </div>
        <div>
          <button id="clearChatBtn" class="secondary">Clear screen</button>
        </div>
      </div>

      <div id="chatWrap" class="chat-wrap"></div>

      <div class="composer">
        <textarea id="messageInput" placeholder="Type your message here..." disabled></textarea>
        <button id="sendBtn" disabled>Send</button>
      </div>
    </main>

    <aside class="rightbar">
      <h3 style="margin-top:0;">Structured Data</h3>

      <div class="card">
        <div class="label">Extracted Fields</div>
        <div id="fieldsBox" class="small">No fields extracted yet.</div>
      </div>

      <div class="card">
        <div class="label">Missing Items</div>
        <div id="missingBox" class="small">None yet.</div>
      </div>

      <div class="card">
        <div class="label">Completion</div>
        <div id="completeBox" class="value">Not complete</div>
      </div>
    </aside>
  </div>

  <script>
    let currentMatterId = null;
    let currentClientId = null;

    const chatWrap = document.getElementById("chatWrap");
    const matterIdEl = document.getElementById("matterId");
    const clientIdEl = document.getElementById("clientId");
    const statusText = document.getElementById("statusText");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const startBtn = document.getElementById("startBtn");
    const createMatterBtn = document.getElementById("createMatterBtn");
    const clearChatBtn = document.getElementById("clearChatBtn");
    const fieldsBox = document.getElementById("fieldsBox");
    const missingBox = document.getElementById("missingBox");
    const completeBox = document.getElementById("completeBox");
    const nextQuestionEl = document.getElementById("nextQuestion");
    const nextOptionsEl = document.getElementById("nextOptions");

    function setStatus(text) {
      statusText.textContent = text;
    }

    function addMessage(role, content) {
      const div = document.createElement("div");
      div.className = "message " + (role === "user" ? "user" : "assistant");
      div.textContent = content;
      chatWrap.appendChild(div);
      chatWrap.scrollTop = chatWrap.scrollHeight;
    }

    function renderFields(fields) {
      const entries = Object.entries(fields || {});
      if (!entries.length) {
        fieldsBox.innerHTML = "No fields extracted yet.";
        return;
      }
      fieldsBox.innerHTML = entries
        .map(([k, v]) => `<div style="margin-bottom:8px;"><strong>${escapeHtml(k)}</strong><br>${escapeHtml(String(v))}</div>`)
        .join("");
    }

    function renderMissing(items) {
      if (!items || !items.length) {
        missingBox.innerHTML = "None.";
        return;
      }
      missingBox.innerHTML = "<ul>" + items.map(item => `<li>${escapeHtml(item)}</li>`).join("") + "</ul>";
    }

    function renderOptions(options) {
      if (!options || !options.length) {
        nextOptionsEl.innerHTML = "";
        return;
      }
      nextOptionsEl.innerHTML = options
        .map((opt, idx) => `<div class="pill">${idx + 1}. ${escapeHtml(String(opt))}</div>`)
        .join("");
    }

    function updateResponsePanels(data) {
      renderFields(data.extracted_fields || {});
      renderMissing(data.missing_items || []);
      completeBox.textContent = data.is_complete ? "Complete" : "Not complete";
      nextQuestionEl.textContent = data.next_question || data.reply || "No question.";
      renderOptions(data.next_options || []);
    }

    function escapeHtml(str) {
      return str
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    async function createMatter() {
      setStatus("Creating test matter...");
      createMatterBtn.disabled = true;

      try {
        const res = await fetch("/test-create-matter", {
          method: "POST"
        });
        if (!res.ok) {
          throw new Error("Failed to create matter");
        }

        const data = await res.json();
        currentMatterId = data.matter_id;
        currentClientId = data.client_id;

        matterIdEl.textContent = currentMatterId;
        clientIdEl.textContent = currentClientId;

        startBtn.disabled = false;
        messageInput.disabled = true;
        sendBtn.disabled = true;

        addMessage("assistant", "Test matter created. Click 'Start intake' to begin.");
        setStatus("Matter created.");
      } catch (err) {
        addMessage("assistant", "Error creating matter: " + err.message);
        setStatus("Error.");
      } finally {
        createMatterBtn.disabled = false;
      }
    }

    async function startIntake() {
      if (!currentMatterId) {
        alert("Create a matter first.");
        return;
      }

      setStatus("Starting intake...");
      startBtn.disabled = true;

      try {
        const res = await fetch(`/matters/${currentMatterId}/start`);
        if (!res.ok) {
          throw new Error("Failed to start intake");
        }

        const data = await res.json();
        addMessage("assistant", data.reply);
        updateResponsePanels(data);

        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();

        setStatus("Intake started.");
      } catch (err) {
        addMessage("assistant", "Error starting intake: " + err.message);
        setStatus("Error.");
        startBtn.disabled = false;
      }
    }

    async function sendMessage() {
      const text = messageInput.value.trim();
      if (!text || !currentMatterId) return;

      addMessage("user", text);
      messageInput.value = "";
      sendBtn.disabled = true;
      setStatus("Sending...");

      try {
        const res = await fetch(`/matters/${currentMatterId}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: text })
        });

        if (!res.ok) {
          throw new Error("Chat request failed");
        }

        const data = await res.json();
        addMessage("assistant", data.reply);
        updateResponsePanels(data);
        setStatus("Reply received.");
      } catch (err) {
        addMessage("assistant", "Error sending message: " + err.message);
        setStatus("Error.");
      } finally {
        sendBtn.disabled = false;
        messageInput.focus();
      }
    }

    createMatterBtn.addEventListener("click", createMatter);
    startBtn.addEventListener("click", startIntake);
    sendBtn.addEventListener("click", sendMessage);

    messageInput.addEventListener("keydown", function(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    });

    clearChatBtn.addEventListener("click", function() {
      chatWrap.innerHTML = "";
      fieldsBox.innerHTML = "No fields extracted yet.";
      missingBox.innerHTML = "None yet.";
      completeBox.textContent = "Not complete";
      nextQuestionEl.textContent = "No question yet.";
      nextOptionsEl.innerHTML = "";
      setStatus("Screen cleared.");
    });
  </script>
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

SKIP_VALUES = {"skip", "not sure", "unknown", ""}

for key, value in extracted_fields.items():
    if value is None:
        continue

    clean_value = str(value).strip()

    # skip handling
    if clean_value.lower() in SKIP_VALUES:
        continue

    # save original field
    upsert_answer(db, matter_id, key, clean_value)
    saved_fields[key] = clean_value

    # special handling for current_date
    if key == "current_date":
        try:
            dt = datetime.strptime(clean_value, "%Y.%m.%d")

            year = dt.strftime("%Y")
            month = dt.strftime("%b")   # Jan, Feb, Mar
            day = dt.strftime("%d")

            upsert_answer(db, matter_id, "year", year)
            upsert_answer(db, matter_id, "month", month)
            upsert_answer(db, matter_id, "date", day)

        except Exception:
            pass

    db.commit()

    assistant_reply = result.get("next_question") or result.get("assistant_reply", "Okay.")
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
    source_documents = load_source_documents()

    known_answers = get_known_answers(db, matter_id)

    result = run_document_driven_intake(
        source_documents=source_documents,
        known_answers=known_answers,
        user_message="Start the intake and ask the first question."
    )

    assistant_reply = result.get("next_question") or result.get("assistant_reply", "Let's begin.")

    missing_items = result.get("missing_items", [])
    next_question = result.get("next_question", "")
    next_options = result.get("next_options", [])
    is_complete = result.get("is_complete", False)

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

@app.post("/test-create-matter")
def create_test_matter(db: Session = Depends(get_db)):
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    client_name = f"Test Client {timestamp}"
    matter_name = f"Test Matter {timestamp}"

    try:
        client = Client(name=client_name)
        db.add(client)
        db.commit()
        db.refresh(client)

        matter = Matter(client_id=client.id, display_name=matter_name)
        db.add(matter)
        db.commit()
        db.refresh(matter)

        return {
            "client_id": client.id,
            "matter_id": matter.id
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create test matter because the test client name already exists.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create test matter: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}