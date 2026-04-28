from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from twelvelabs import TwelveLabs
from twelvelabs.types import ResponseFormat
from prompts import Prompts
import asyncio
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

class AnalyzeRequest(BaseModel):
    video_path: str

# ------------------------------------------------------------------------- GEMINI -------------------------------------------------------------------------


# @app.post("/gemini_analysis")
async def gemini_analysis(video_path: str):
    
    print(f"Received video_path: {video_path}")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    video_file = client.files.upload(
        file=video_path,
        config={"mime_type": "video/mp4"}
    )
    print(f"Uploaded: {video_file.name}, state: {video_file.state}")

    while video_file.state.name == "PROCESSING":
        print("Waiting for file to process...")
        await asyncio.sleep(3)
        video_file = client.files.get(name=video_file.name)
    
    if video_file.state.name == "FAILED":
        raise RuntimeError("Gemini file processing failed")

    print("File ready, analyzing...")

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part(file_data=types.FileData(file_uri=video_file.uri)),
            types.Part(text=Prompts.GEMINI_ANALYSIS_PROMPT)
        ]
    )
    print(response.text)
    
    client.files.delete(name=video_file.name)

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": response.text}
    
    
class GeminiCodeRequest(BaseModel):
    algorithm: str
    
@app.post("/gemini_code")
def gemini_code(request: GeminiCodeRequest):
    print(f"Received algorithm: {request.algorithm}")
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=Prompts.GEMINI_CODE_PROMPT.format(algorithm=request.algorithm)
    )
    print(response.text)
    return response.text


def gemini_modify_code(code: str, twelvelabs_errors: dict, gemini_errors: dict):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    print("writing new code...")
    
    if gemini_errors["passed"] == True and twelvelabs_errors["passed"] == True:
        print("NO ERRORS TO FIX")
    else:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", contents=Prompts.GEMINI_MODIFY_CODE_PROMPT.format(
                code=code,
                twelvelabs_errors=json.dumps(twelvelabs_errors),
                gemini_errors=json.dumps(gemini_errors)
            )
        )
        print("new code written")
        print(response.text)

# ------------------------------------------------------------------------- TWELVE LABS -------------------------------------------------------------------------


client = TwelveLabs(api_key=os.getenv("TWELVE_LABS_API_KEY"))

INDEX_NAME = "maniflow-analysis"

existing_indexes = client.indexes.list()

my_index = next((idx for idx in existing_indexes if idx.index_name == INDEX_NAME), None)

if my_index:
    INDEX_ID = my_index.id
    print(f"Found existing index: {INDEX_ID}")
else:
    new_index = client.indexes.create(
        index_name=INDEX_NAME,
        models=[{"model_name": "pegasus1.2", "model_options": ["visual", "audio"]}]
    )
    INDEX_ID = new_index.id
    print(f"Created new index: {INDEX_ID}")

# @app.post("/tl_analysis")
async def tl_analysis(video_path: str):
    
    with open(video_path, "rb") as video_file:
        asset = client.assets.create(
            method="direct",
            file=video_file
        )
            
    print(f"Upload successful! Task ID: {asset.id}")
    print(f"Created asset: {asset.id}")

    indexed_asset = client.indexes.indexed_assets.create(
        index_id=INDEX_ID,
        asset_id=asset.id,
    )
    print(f"Indexing asset: {indexed_asset.id}")

    print("Waiting for indexing...")
    while True:
        indexed_asset = client.indexes.indexed_assets.retrieve(
            index_id=INDEX_ID,
            indexed_asset_id=indexed_asset.id
        )
        print(f"  Status: {indexed_asset.status}")
        if indexed_asset.status == "ready":
            print("Indexing complete!")
            break
        elif indexed_asset.status == "failed":
            raise RuntimeError("Indexing failed")
        await asyncio.sleep(5)

    text = client.analyze(
        video_id=indexed_asset.id,
        prompt=Prompts.TWELVE_LABS_ANALYSIS_PROMPT,
        response_format=ResponseFormat(
            type="json_schema",
            json_schema={
                "type": "object",
                "properties": {
                    "passed": {"type": "boolean"},
                    "overall_summary": {"type": "string"},
                    "errors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "severity": {"type": "string"},
                                "description": {"type": "string"},
                                "timestamp": {"type": "string"},
                                "suggested_fix": {"type": "string"}
                            }
                        }
                    },
                    "passed_checks": {"type": "array", "items": {"type": "string"}},
                    "iteration_recommendation": {"type": "string"}
                }
            }
        ),
    )
    
    print(text.model_dump())

    return text.model_dump()


# def render_video(code: str, scene: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.fetch("/api/render", json={"code": code, "scene": scene})
#         return response.json()

# ------------------------------------------------------------------------- MAIN -------------------------------------------------------------------------
class Analyze(BaseModel):
    video_path: str
    code: str

@app.post("/analyze")
async def analyze(body: Analyze):
    
    print("woijgowejoiewoiwjfiwejofiwejoijweoij")
    
    gemini_response, tl_response = await asyncio.gather(
        gemini_analysis(body.video_path),
        tl_analysis(body.video_path)
    )
    
    gemini_modified_code = gemini_modify_code(body.code, tl_response, gemini_response)
    
    print(f"Gemini modified code: {gemini_modified_code}")
    
    # const res = await fetch("/api/render", {
    #   method: "POST",
    #   headers: { "Content-Type": "application/json" },
    #   body: JSON.stringify({ code, scene }),
    # });
    
    return{
        "gemini_response": gemini_response,
        "tl_response": tl_response
    }