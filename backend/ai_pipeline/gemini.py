from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# def generate_manim_code(prompt):
#     response = client.models.generate_content(
#         model="gemini-3-flash-preview",
#         contents=prompt)
    
#     return response.text


prompt = '''
    Write me Manim code to visualize hoare quicksort on this array: [3, 1, 4, 10, 5, 9, 2, 6, 5, 7, 5].
    Include text in the video to explain the step-by-step process of the visualization. label any important variables and values.
    Don't output anything else, just the code.
'''

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt
)

print(response.text)