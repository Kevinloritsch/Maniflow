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

load_dotenv()

def gemini_code():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=Prompts.GEMINI_CODE_PROMPT
    )
    print(response.text)
    return response.text

gemini_code()