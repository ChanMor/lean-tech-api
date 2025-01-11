from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

import requests
import os

load_dotenv()

PERPLEXITY_API_KEY=os.getenv("PERPLEXITY_API_KEY")

app = FastAPI()

@app.get("/")
async def connect():
    return {"status": "Successful"}

@app.get("/retrieve/cases")
async def retrieve_cases(name: str):

    prompt = f"""
        get cases of {name} from credible sources such as news articles, governement and .ph sites
    """

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
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
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    try:
        response = requests.post(url, json=payload, headers=headers)
        return {"status": "success", "cases": response.text}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail="Error")









