from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import requests
import json
import re
import os

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

app = FastAPI()

# Main endpoint to retrieve all information
@app.get("/retrieve/summary")
async def retrieve_summary(name: str):
    # Retrieve data from all other endpoints
    careers = await retrieve_career(name)
    dynasty = await retrieve_dynasty(name)
    legislations = await retrieve_bills(name)
    education = await retrieve_education(name)
    projects = await retrieve_projects(name)
    cases = await retrieve_cases(name)

    # Combine data into a single response, leaving empty fields if no data is found
    summary = {
        "commonName": name,
        "legalName": name,  # Assuming legalName is the same as commonName
        "description": f"Detailed summary of {name}'s life, career, education, and significant political and legal information.",
        "cases": cases.get("data", []),
        "careers": careers.get("data", []),
        "dynasty": dynasty.get("data", []),
        "legislations": legislations.get("data", []),
        "education": education.get("data", []),
        "projects": projects.get("data", []),
    }
    
    # Ensure that fields that did not return any data are empty strings
    for key in summary:
        if not summary[key]:
            summary[key] = ""

    return {"status": "success", "data": summary}

# Helper function to avoid code duplication
async def get_response(prompt: str):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Eleborate on description asked by users. Generate it strictly as JSON following the requested schema. If no data is found, leave fields empty (empty string or empty list) but **never fabricate data** or **generate hallucinations**. Never use wikipedia as source. Don't output anything other than the json format required. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai", ".ph", "gov.ph", "edu.ph", "gov", "ph", "mb.com.ph", "gmanetwork.com", "inquirer.net", "pna.gov.ph", "rappler.com", "abs-cbn.com", "philstar.com", "manilatimes.net" ], 
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

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()


        json_string = data["choices"][0]["message"]["content"]

        match = re.search(r"```(.*?)```", json_string, re.DOTALL)
        if match:
            json_string = match.group(1)
        else:
            json_string = ""

        json_string = json_string.strip("```json\n").strip("\n```")

        print(json_string)

        json_object = json.loads(json_string)
        return {"status": "success", "data": json_object}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail="Error retrieving data")

# Define endpoints for specific information requests

@app.get("/retrieve/cases")
async def retrieve_cases(name: str):
    prompt = f"""
        Get me all the legal cases involving {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Cases refers to the criminal, civil, administrative, tax evasion, graft, corruption, etc which is something negative. This refers to something negative associated that comes with government and legal action. Elaborate with description. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "cases": [
            {{
                "title": <String>,
                "description": <String>,
                "dateFiled": <String>,
                "link": <String>  # URL of the reliable source, preferably from government or trusted news websites (avoid Wikipedia)
            }},
            ...
        ]}}
        If no cases are found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)

@app.get("/retrieve/dynasty")
async def retrieve_dynasty(name: str):
    prompt = f"""
        Get me all the political relatives and dynasty details of {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. This refers to the person biologically related to the person requested and should be an actual person in a government position or previously held government position. Elaborate with description. Never use wikipedia. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "dynasty": [
            {{
                "name": <String>,
                "relation": <String>,
                "currentPosition": <String>,
                "link": <String>  # URL of the reliable source (government, news articles, .ph domains)
            }},
            ...
        ]}}
        If no dynasty details are found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)

@app.get("/retrieve/career")
async def retrieve_career(name: str):
    prompt = f"""
        Get me all career details of {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Elaborate with description. Never use wikipedia. Return the data in strict JSON format following the schema:
        {{
        "careers": [
            {{
                "title": <String>,
                "duration": <String>,
                "description": <String>,
                "link": <String>  # URL of the credible source
            }},
            ...
        ]}}
        If no career information is found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)

@app.get("/retrieve/projects")
async def retrieve_projects(name: str):
    prompt = f"""
        Get me all the projects associated with {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Projects refer to the actual government initiatives such as programs, outreach, and etc. Never use wikipedia. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "projects": [
            {{
                "title": <String>,
                "duration": <String>,
                "description": <String>,
                "status": <String>,
                "link": <String>  # URL of the credible source
            }},
            ...
        ]}}
        If no project information is found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)

@app.get("/retrieve/bills")
async def retrieve_bills(name: str):
    prompt = f"""
        Get me all the bills related to {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Elaborate  description. This refers to authored bills as well as co-authored bills. Clearly indicate in description is authored or co-authored. Never use wikipedia. Return the data in strict JSON format following the schema:
        {{
        "legislations": [
            {{
                "title": <String>,
                "status": <String>,
                "description": <String>,
                "dateFiled": <Date>,
                "link": <String>  # URL of the reliable source
            }},
            ...
        ]}}
        If no bills are found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)

@app.get("/retrieve/education")
async def retrieve_education(name: str):
    prompt = f"""
        Get me all the educational details of {name} from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Elaborate description. Never use wikipedia. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "education": [
            {{
                "attained": <String>,  # e.g., Bachelor's degree, High School diploma, etc.
                "school": <String>,
                "dateCompleted": <String>,
                "link": <String>  # URL of the reliable source
            }},
            ...
        ]}}
        If no educational information is found, leave the fields empty (e.g., "" for string fields, [] for list fields).
        """
    return await get_response(prompt)
