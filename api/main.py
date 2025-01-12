from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from google.cloud import translate_v2

import asyncio
import copy
import tempfile
import hashlib
import requests
import base64
import json
import re
import os
from pydantic import BaseModel
load_dotenv()
import redis
import copy

rd = redis.Redis(host=os.getenv("REDIS_HOST"), port=18810, db="FranzChristian-free-db")

def normalize_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.strip().lower())

def generate_cache_key(name: str) -> str:
    normalized_name = normalize_name(name)
    return hashlib.md5(normalized_name.encode('utf-8')).hexdigest()


PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
key_base64 = os.getenv("GOOGLE_API_BASE64")

key_json = base64.b64decode(key_base64)


with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    tmp_file.write(key_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_file.name

translate_client = translate_v2.Client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow sending cookies or other credentials
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def connect():
    return {"status": "success"}

# Main endpoint to retrieve all information
@app.get("/retrieve/summary")
async def retrieve_summary(name: str, province: str = "", municipality: str = ""):
    cache_key = generate_cache_key(name)
    
    # Try to get the cached data from Redis
    cached_data = rd.get(cache_key)
    
    if cached_data:
        # If cached data exists, parse the JSON string back into a Python object
        return {"status": "success", "data": json.loads(cached_data)}
    
    # Retrieve data from all other endpoints

    names, desc, careers, dynasty, legislations, education, projects, cases = await asyncio.gather(
        retrieve_names(name, province, municipality),
        retrieve_desc(name, province, municipality),
        retrieve_career(name, province, municipality),
        retrieve_dynasty(name, province, municipality),
        retrieve_bills(name, province, municipality),
        retrieve_education(name, province, municipality),
        retrieve_projects(name,province, municipality),
        retrieve_cases(name, province, municipality)
    )


    nameDict = names.get("data", [])

    # Combine data into a single response, leaving empty fields if no data is found
    summary = {
        "commonName": nameDict.get("commonName", []),
        "legalName": nameDict.get("legalName", []),
        "description": desc.get("data", []),
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

    rd.set(cache_key, json.dumps(summary))


    return {"status": "success", "data": summary}

# Helper function to avoid code duplication
async def get_response(prompt: str):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Eleborate on description asked by users. Generate it strictly as JSON following the requested schema. If no data is found, leave fields empty (empty string or empty list) but **never fabricate data** or **generate hallucinations**. Never use wikipedia and britanica as source. Don't output anything other than the json format required. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net."
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
        response = await asyncio.to_thread(requests.post, url, json=payload, headers=headers, timeout=30)

        data = response.json()

        print(data)
        json_string = data["choices"][0]["message"]["content"]

        match = re.search(r"```(.*?)```", json_string, re.DOTALL)
        if match:
            json_string = match.group(1)

        json_string = json_string.strip("```json\n").strip("\n```")

        print(json_string)

        json_object = json.loads(json_string)
        return {"status": "success", "data": json_object}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail="error")

# Define endpoints for specific information requests

@app.get("/retrieve/cases")
async def retrieve_cases(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me all the legal cases involving {name} ({province} {municipality}) from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Be neutral in tone without bias. This does not have to be an active case. Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Cases refers to the criminal, civil, administrative, tax evasion, graft, corruption, etc which is something negative. This refers to something negative associated that comes with government and legal action. Elaborate with description. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "cases": [
            {{
                "title": <String>,
                "description": <String>,
                "dateFiled": <String>,
                "link": <String>  # URL of the reliable source, preferably from government or trusted news websites (avoid Wikipedia and britanica)
            }},
            ...
        ]}}
        If no cases are found, maintain the schema the fields set as empty string "".
        """
    return await get_response(prompt)

@app.get("/retrieve/dynasty")
async def retrieve_dynasty(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me all the political relatives and dynasty details of {name} ({province} {municipality}) from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Be neutral in tone without bias. Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. This refers to the person biologically related to the person requested and should be an actual person in a government position or previously held government position. They may have also held position in provincial government positions. This can refer to mother, father, son, daughter, cousin, uncle, aunt, etc. Elaborate with description. Never use wikipedia and britanica. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
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
async def retrieve_career(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me all career details of {name} ({province} {municipality}) from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Be neutral in tone without bias.  Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Elaborate with description. Never use wikipedia and britanica. Career may refer not only to political or government position but also non government position. Return the data in strict JSON format following the schema:
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
        If no career information is found, maintain the schema the fields set as empty string "".
        """
    return await get_response(prompt)

@app.get("/retrieve/projects")
async def retrieve_projects(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me all the projects associated with {name} ({province} {municipality}) from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Be neutral in tone without bias. Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Projects refer to the actual government initiatives such as programs, outreach, and etc. Never use wikipedia and britanica. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
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
        If no project information is found, maintain the schema the fields set as empty string "".
        """
    return await get_response(prompt)

@app.get("/retrieve/bills")
async def retrieve_bills(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
       Get me all the bills related to {name} he authored and one he co-authored were passed into law. Return the information strictly from credible Philippine sources, including senate.gov.ph** and verafiles.org. Use the official data available from these sites and provide valid links. Elaborate  description. Be neutral in tone without bias. Clearly state whether the bill was **authored or co-authored. Provide an **elaborate description** of each bill, including any additional context or legislative importance. Never use wikipedia and britanica. Return the data in strict JSON format following the schema:
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
        If no bills are found, maintain the schema the fields set as empty string "".
        """
    return await get_response(prompt)

@app.get("/retrieve/education")
async def retrieve_education(name: str, province: str, municipality: str):
    
    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me all the educational attainments such as college degrees of {name} ({province} {municipality}) from **credible article sources such as news articles in the Philippines and government websites** (e.g., .ph sources). Make sure college degree was completed. Be neutral. Be neutral in tone without bias.  Get information strictly only from these reputable Philippine sources: .ph, gov.ph, edu.ph, gov, ph, mb.com.ph, gmanetwork.com, inquirer.net, pna.gov.ph, rappler.com, abs-cbn.com, philstar.com, and manilatimes.net. Elaborate description. Never use wikipedia and britanica. If no information found just return the schema requested with empty strings as values in each fields. No text outside of the required json. Return the data in strict JSON format following the schema:
        {{
        "education": [
            {{
                "attained": <String>, 
                "school": <String>,
                "dateCompleted": <String>,
                "link": <String>  # URL of the reliable source
            }},
            ...
        ]}}
        If no educational information is found, maintain the schema the fields set as empty string "".
        """
    return await get_response(prompt)

  
class TranslationRequest(BaseModel):
    to_translate: dict
    target_language: str

@app.post("/translate")
async def translate(request: TranslationRequest):
    orig = request.to_translate
    target_language = request.target_language

    cache_key = hashlib.md5(json.dumps(orig).encode("utf-8")).hexdigest()
    to_translate = copy.deepcopy(orig)
    # Try to get the cached data from Redis
    cached_data = rd.get(cache_key)
    
    if cached_data:
        # If cached data exists, parse the JSON string back into a Python object
        return {"status": "success", "translatedText": json.loads(cached_data)}

    try:
        def translate_field(field: str) -> str:
            if field:
                print(translate_client.translate(field, target_language=target_language)['translatedText'])
                return translate_client.translate(field, target_language=target_language)['translatedText']
            return ""

        if "description" in to_translate:
            to_translate["description"] ["desc"]= translate_field(to_translate["description"]["desc"])

        if "careers" in to_translate:
            for career in to_translate["careers"] ["careers"]:
                career["title"] = translate_field(career.get("title", ""))
                career["description"] = translate_field(career.get("description", ""))

        if "dynasty" in to_translate:
            for relative in to_translate["dynasty"] ["dynasty"]:
                relative["relation"] = translate_field(relative.get("relation", ""))
                relative["currentPosition"] = translate_field(relative.get("currentPosition", ""))

        if "cases" in to_translate:
            for case in to_translate["cases"]["cases"]:
                case["description"] = translate_field(case.get("description", ""))

        if "legislations" in to_translate:
            for legislation in to_translate["legislations"]["legislations"]:
                legislation["description"] = translate_field(legislation.get("description", ""))

        if "projects" in to_translate:
            for project in to_translate["projects"]["projects"]:
                project["description"] = translate_field(project.get("description", ""))

        rd.set(cache_key, json.dumps(to_translate))
        print(to_translate)
        return {"status": "Successful", "translatedText": to_translate}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {e}")



@app.get("/retrieve/names")
async def retrieve_names(name: str, province: str, municipality: str):

    if not province:
        province = ""

    if not municipality:
        municipality = ""

    prompt = f"""
        Get me the common name and the full legal name of {name} ({province} {municipality}). Be neutral in tone without bias. Get from wikipedia or other sources the full name. No text outside of the required JSON. Return the data in strict JSON format following the schema:
        {{
            "commonName": <String>,
            "legalName": <String>
        }}
        If no info is found, maintain the schema the fields set as empty string "".
    """
    return await get_response(prompt)

@app.get("/compare")
async def compare(name1: str, name2: str):

    cache_key1 = generate_cache_key(name1)
    
    # Try to get the cached data from Redis
    cached_data1 = rd.get(cache_key1)
    
    if cached_data1:
        # If cached data exists, parse the JSON string back into a Python object
        summary1 = json.loads(cached_data1)
    else:
        summary1 = await retrieve_summary(name1)


    cache_key2 = generate_cache_key(name2)
    
    # Try to get the cached data from Redis
    cached_data2 = rd.get(cache_key2)
    
    if cached_data2:
        # If cached data exists, parse the JSON string back into a Python object
        summary2 = json.loads(cached_data2)
    else:
        summary2 = await retrieve_summary(name2)

    return {"status": "success", "data": [summary1, summary2]}


@app.get("/retrieve/desc")
async def retrieve_desc(name: str, province, municipality):
    prompt = f"""
        Get me the short description of {name} ({province} {municipality}). Do not get data from wikipedia. Be neutral in tone without bias. No text outside of the required JSON. Return the data in strict JSON format following the schema:
        {{
            "desc": <String>
        }}
        If no info is found, maintain the schema the fields set as empty string "".
    """
    return await get_response(prompt)





@app.get("/trending")
async def get_trending_politicians():
    
    cache_key = "top_10"
    
    # Try to get the cached data from Redis
    cached_data = rd.get(cache_key)
    
    if cached_data:
        # If cached data exists, parse the JSON string back into a Python object
        return {"status": "success", "data": json.loads(cached_data)}
    
    prompt = f"""
        Give me the top 10 most popular and talked about philippine politicians today. No text outside of the required JSON. Return the data in strict JSON format following the schema:
        {{
            "trending": [<String>] #list of strings
        }}
        If no info is found, just return {{"trending": []}} empty string"".
    """

    json_obj = await get_response(prompt)
    
    rd.set(cache_key, json.dumps(json_obj))
       
    return {"status": "success", "data": json_obj}