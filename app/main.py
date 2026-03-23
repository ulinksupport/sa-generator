from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

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

@app.get("/health")
def health():
    return {"status": "ok"}