from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel

import requests
import os


from google.cloud import translate_v2


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"key.json"
translate_client = translate_v2.Client()

load_dotenv()

PERPLEXITY_API_KEY=os.getenv("PERPLEXITY_API_KEY")

app = FastAPI()

@app.get("/")
async def connect():
    return {"status": "Successful"}

@app.get("/retrieve/cases")
async def retrieve_cases(name: str):

    prompt = f"""
        get me all the cases from {name} and return it in a json format:
        {{
        cases: [
        {{
            title: <String>, 
            desc: <String>,
            date: <String>,
            article/website URL: <String>
        }},
        {{
            title: <String>, 
            desc: <String>,
            date: <String>,
            article/website URL: <String>
        }},
        ...
        ]
        }}
        Articles or website sources must be reliable. Make the desc more descriptive. site must not include wikipedia. Include from government websites
    """

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise. Generate it as json"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        json_string = data["choices"][0]["message"]["content"]
        json_string = json_string.strip("```json\n").strip("\n```")

        json_object = json.loads(json_string)

        return {"status": "success", "data": json_object}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail="Error")

@app.get("/retrieve/dynasty")
async def retreve_dynasty():
    return {"status": "Successful"}

@app.get("/retrieve/career")
async def retreve_career():
    return {"status": "Successful"}

@app.get("/retrieve/projects")
async def retreve_projects():
    return {"status": "Successful"}

@app.get("/retrieve/bills")
async def retreve_bills():
    return {"status": "Successful"}

@app.get("/retrieve/education")
async def retreve_education():
    return {"status": "Successful"}

 
class TranslationRequest(BaseModel):
    to_translate: dict
    target_language: str




@app.post("/translate")
async def translate(request: TranslationRequest):
    toTranslate = request.to_translate
    targetLanguage = request.target_language
    
    for fields in toTranslate:
        for k,v in fields:
            fields[k] = translate_client.translate(v, target_language=targetLanguage)
    
    
     
    
    return {"status": "Successful", "translatedText": translatedText}
