# import os
# import shutil
# import pandas as pd
# import PyPDF2
# from fastapi import FastAPI, File, UploadFile, Form
# from typing import List, Dict
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# import anthropic
#
# # Load environment variables
# load_dotenv()
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
#
# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)
#
# # Initialize FastAPI
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=['*'],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # Initialize Claude AI client
# client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
#
#
# # Generate response using Claude AI
# def generate_claude_response(kpi: str, data: str) -> str:
#     prompt_template = f"""
#     Analyze the data for {kpi} and summarize key trends in **1 concise line**.
#
#     Data: {data}
#
#     Identify patterns and provide business implications concisely.
#     """
#
#     response = client.messages.create(
#         model="claude-3-opus-20240229",  # Choose model: "claude-3-haiku", "claude-3-sonnet", or "claude-3-opus"
#         max_tokens=50,  # Keep response short
#         messages=[{"role": "user", "content": prompt_template}]
#     )
#
#     return response.content[0].text.strip() if response.content else "No response from Claude."
#
#
# # Extract text from PDFs
# def extract_text_from_pdf(file_path: str) -> str:
#     try:
#         text = []
#         with open(file_path, "rb") as file:
#             pdf_reader = PyPDF2.PdfReader(file)
#             for page in pdf_reader.pages:
#                 text.append(page.extract_text())
#         return "\n".join(text).strip() if text else "No text extracted from PDF."
#     except Exception as e:
#         return f"Error extracting text: {e}"
#
#
# # Process PDF files
# def process_pdf(file_path: str, kpis: List[str]) -> Dict[str, str]:
#     extracted_text = extract_text_from_pdf(file_path)
#
#     insights = {}
#     for kpi in kpis:
#         response = generate_claude_response(kpi, extracted_text)
#         insights[kpi] = response if response else "No relevant insight."
#
#     return insights
#
#
# # Process CSV/Excel files
# def process_tabular_data(file_path: str, kpis: List[str]) -> Dict[str, str]:
#     try:
#         print("trying")
#         df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
#         insights = {}
#         for kpi in kpis:
#             matched_columns = [col for col in df.columns if kpi.strip().lower() in col.lower()]
#             if matched_columns:
#                 kpi_data = df[matched_columns].to_dict()
#                 insights[kpi] = generate_claude_response(kpi, str(kpi_data))
#             else:
#                 insights[kpi] = "KPI not found in document."
#
#         return insights
#     except Exception as e:
#         return {"error": str(e)}
#
#
# # File Upload API
# @app.post("/upload/")
# async def upload_files(files: List[UploadFile] = File(...), kpis: str = Form(...)):
#     kpi_list = [kpi.strip() for kpi in kpis.split(",")]
#     results = {}
#
#     for file in files:
#         file_path = os.path.join(UPLOAD_DIR, file.filename)
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#
#         if file.filename.endswith((".csv", ".xlsx")):
#             insights = process_tabular_data(file_path, kpi_list)
#         elif file.filename.endswith(".pdf"):
#             insights = process_pdf(file_path, kpi_list)
#         else:
#             insights = "Unsupported file format."
#
#         results[file.filename] = insights
#
#     return {"status": "success", "data": results}
#
#


import os
import shutil
import pandas as pd
import PyPDF2
from typing import List, Dict
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Directories
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML template folder
templates = Jinja2Templates(directory="templates")

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Claude AI client
client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

def generate_claude_response(kpi: str, data: str) -> str:
    prompt_template = f"""
    Analyze the data for {kpi} and summarize key trends in **1 concise line**.

    Data: {data}

    Identify patterns and provide business implications concisely.
    """

    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt_template}]
    )

    return response.content[0].text.strip() if response.content else "No response from Claude."


def extract_text_from_pdf(file_path: str) -> str:
    try:
        text = []
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return "\n".join(text).strip() if text else "No text extracted from PDF."
    except Exception as e:
        return f"Error extracting text: {e}"


def process_pdf(file_path: str, kpis: List[str]) -> Dict[str, str]:
    extracted_text = extract_text_from_pdf(file_path)
    insights = {}
    for kpi in kpis:
        response = generate_claude_response(kpi, extracted_text)
        insights[kpi] = response if response else "No relevant insight."
    return insights


def process_tabular_data(file_path: str, kpis: List[str]) -> Dict[str, str]:
    try:
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
        insights = {}
        for kpi in kpis:
            matched_columns = [col for col in df.columns if kpi.strip().lower() in col.lower()]
            if matched_columns:
                kpi_data = df[matched_columns].to_dict()
                insights[kpi] = generate_claude_response(kpi, str(kpi_data))
            else:
                insights[kpi] = "KPI not found in document."
        return insights
    except Exception as e:
        return {"error": str(e)}


@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...), kpis: str = Form(...)):
    kpi_list = [kpi.strip() for kpi in kpis.split(",")]
    results = {}

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if file.filename.endswith((".csv", ".xlsx")):
            insights = process_tabular_data(file_path, kpi_list)
        elif file.filename.endswith(".pdf"):
            insights = process_pdf(file_path, kpi_list)
        else:
            insights = "Unsupported file format."

        results[file.filename] = insights

    return {"status": "success", "data": results}
