# Politician Info API

This FastAPI project provides an API for retrieving detailed information about politicians, including their careers, legal cases, political dynasty, education, bills, projects, and more. It also supports translations and trending data, using Redis for caching and Perplexity AI for advanced data retrieval.

## Members
- Castillo, Combalicer, Lleva, Morelos

## Endpoints

### 1. **`GET /`**
- **Purpose**: Health check endpoint to verify the API is running.
- **Response**: 
    ```json
    {
      "status": "success"
    }
    ```

### 2. **`GET /retrieve/summary`**
- **Purpose**: Retrieves a detailed summary of a politician, including career, education, projects, legal cases, etc., for a given name, province, and municipality.
- **Response**:
    ```json
    {
      "status": "success",
      "data": {
        "commonName": "<String>",
        "legalName": "<String>",
        "description": "<String>",
        "cases": "<Array>",
        "careers": "<Array>",
        "dynasty": "<Array>",
        "legislations": "<Array>",
        "education": "<Array>",
        "projects": "<Array>"
      }
    }
    ```
- **Caching**: The result is cached in Redis for faster subsequent retrieval.

### 3. **`GET /retrieve/cases`**
- **Purpose**: Retrieves legal cases involving a politician from credible sources (e.g., government websites, news outlets).
- **Response**:
    ```json
    {
      "cases": [
        {
          "title": "<String>",
          "description": "<String>",
          "dateFiled": "<String>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 4. **`GET /retrieve/dynasty`**
- **Purpose**: Retrieves information about the political relatives (dynasty) of a politician, such as their relations and positions.
- **Response**:
    ```json
    {
      "dynasty": [
        {
          "name": "<String>",
          "relation": "<String>",
          "currentPosition": "<String>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 5. **`GET /retrieve/career`**
- **Purpose**: Retrieves career details of a politician, including political and non-political roles.
- **Response**:
    ```json
    {
      "careers": [
        {
          "title": "<String>",
          "duration": "<String>",
          "description": "<String>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 6. **`GET /retrieve/projects`**
- **Purpose**: Retrieves information on government projects or initiatives associated with a politician.
- **Response**:
    ```json
    {
      "projects": [
        {
          "title": "<String>",
          "duration": "<String>",
          "description": "<String>",
          "status": "<String>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 7. **`GET /retrieve/bills`**
- **Purpose**: Retrieves bills authored or co-authored by a politician that have been passed into law.
- **Response**:
    ```json
    {
      "legislations": [
        {
          "title": "<String>",
          "status": "<String>",
          "description": "<String>",
          "dateFiled": "<Date>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 8. **`GET /retrieve/education`**
- **Purpose**: Retrieves educational details of a politician, such as college degrees and institutions attended.
- **Response**:
    ```json
    {
      "education": [
        {
          "attained": "<String>",
          "school": "<String>",
          "dateCompleted": "<String>",
          "link": "<String>"  # Source link
        }
      ]
    }
    ```

### 9. **`POST /translate`**
- **Purpose**: Translates a given dictionary of fields (e.g., descriptions, careers) from one language to another.
- **Request Body**:
    ```json
    {
      "to_translate": { 
        "description": { "desc": "<String>" },
        "careers": [ { "title": "<String>", "description": "<String>" } ]
      },
      "target_language": "<String>"  # Target language code (e.g., 'en', 'tl')
    }
    ```
- **Response**:
    ```json
    {
      "status": "success",
      "translatedText": {
        "description": { "desc": "<Translated String>" },
        "careers": [ { "title": "<Translated String>", "description": "<Translated String>" } ]
      }
    }
    ```

### 10. **`GET /retrieve/names`**
- **Purpose**: Retrieves the common name and full legal name of a politician.
- **Response**:
    ```json
    {
      "commonName": "<String>",
      "legalName": "<String>"
    }
    ```

### 11. **`GET /compare`**
- **Purpose**: Compares two politicians by retrieving their summary data and displaying them side-by-side.
- **Response**:
    ```json
    {
      "status": "success",
      "data": [ 
        { "commonName": "<String>", "legalName": "<String>", "description": "<String>" }, 
        { "commonName": "<String>", "legalName": "<String>", "description": "<String>" } 
      ]
    }
    ```

### 12. **`GET /retrieve/desc`**
- **Purpose**: Retrieves a short description of a politician for a given name, province, and municipality.
- **Response**:
    ```json
    {
      "desc": "<String>"
    }
    ```

### 13. **`GET /trending`**
- **Purpose**: Retrieves a list of the top 10 most popular and talked-about politicians in the Philippines today.
- **Response**:
    ```json
    {
      "status": "success",
      "data": {
        "trending": ["<String>", "<String>", ...]  # List of politician names
      }
    }
    ```
- **Caching**: The result is cached in Redis for faster subsequent retrieval.

---

## Dependencies

- **FastAPI**: The web framework used to build the API.
- **Redis**: Used for caching data to improve performance.
- **Google Cloud Translate API**: Used for translating text.
- **Perplexity API**: Used for retrieving detailed summaries and descriptions of politicians.
- **Pydantic**: Used for data validation and serialization.

### License
This project is licensed under the MIT License - see the LICENSE file for details.
