from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
from pydantic import BaseModel

app = FastAPI()

class UploadResponse(BaseModel):
    id: str
    object: str
    purpose: str
    filename: str
    bytes: int
    created_at: int

# Replace this with your actual OpenAI API key
OPENAI_API_KEY = "your-openai-api-key"

@app.post("/upload-file/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), purpose: str = "user_data"):
    if purpose not in ["assistants", "batch", "fine-tune", "vision", "user_data", "evals"]:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    files = {
        'file': (file.filename, file.file, file.content_type),
        'purpose': (None, purpose)
    }

    response = requests.post("https://api.openai.com/v1/files", headers=headers, files=files)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()

# To run the app, use the command: uvicorn your_script_name:app --reload