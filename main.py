import os
import uuid
import boto3
import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from huggingface_hub import InferenceClient

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

S3_BUCKET = "rezum.analyzer"
client = InferenceClient(api_key=os.getenv("API_KEY"))

@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend Running"}

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="ap-south-1"
    )
    s3_key = None
    try:
        file_content = await file.read()
        s3_key = f"resumes/{uuid.uuid4().hex}.pdf"

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType="application/pdf"
        )

        temp_file = f"temp_{uuid.uuid4().hex}.pdf"
        s3_client.download_file(S3_BUCKET, s3_key, temp_file)

        extracted_text = ""
        with pdfplumber.open(temp_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        os.remove(temp_file)

        prompt = f"""
Analyze this resume and provide:
1. Resume Score (0-100)
2. Top Strengths
3. Missing Skills
4. Improvement Suggestions
5. Career Recommendations

Resume:
{extracted_text[:1500]}
"""
        response = client.chat_completion(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_feedback = response.choices[0].message.content

        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

        return JSONResponse(
            content={
                "filename": file.filename,
                "resume_text": extracted_text[:1000],
                "ai_feedback": ai_feedback
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        if s3_key:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        return JSONResponse(
            content={"error": str(e)},
            headers={"Access-Control-Allow-Origin": "*"}
        )