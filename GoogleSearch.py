#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CSE_ID = os.getenv("GOOGLE_SEARCH_CSE_ID")
# Force UTF-8 encoding for Python in Windows
os.environ["PYTHONIOENCODING"] = "utf-8"

def google_search(api_key, cse_id, query, num_results=10, max_results=500, last_days=180, language="lang_zh-TW", country="countryTW"):
    """
    Perform a Google Custom Search using the Custom Search JSON API with date range, language, and country filter.

    Args:
        api_key (str): Your Google API key.
        cse_id (str): Your Custom Search Engine ID.
        query (str): The search query.
        num_results (int): Number of results per request (max is 10).
        max_results (int): Maximum total results to retrieve (default is 500).
        last_days (int): Number of days to restrict the search to recent results.
        language (str): Language filter (e.g., lang_zh-TW for Traditional Chinese).
        country (str): Country restriction (e.g., countryTW for Taiwan).

    Returns:
        list: A list of search results.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    results = []
    date_limit = f"d{last_days}"  # Restrict results to the last `last_days` days

    for start in range(1, max_results + 1, num_results):
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num_results,
            "start": start,
            "dateRestrict": date_limit,
            "sort": "date",
            "lr": language,  # Language filter for Traditional Chinese
            "cr": country    # Country restriction to Taiwan
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                results.extend(data["items"])
            else:
                print("No more results.")
                break
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break
        if len(results) >= max_results:
            break
    return results[:max_results]

def display_results(results):
    """
    Display search results in a readable format.

    Args:
        results (list): A list of search result items.
    """
    for idx, item in enumerate(results, start=1):
        print(f"Result {idx}:")
        print(f"Title: {item.get('title')}")
        print(f"Link: {item.get('link')}")
        print(f"Snippet: {item.get('snippet')}\n")
        print("-" * 80)

QUERY = "得標統計表 T004 filetype:pdf"

# Perform the search for the last 180 days, limited to Traditional Chinese and Taiwan, and get up to 500 results
search_results = google_search(GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CSE_ID, QUERY, max_results=500, last_days=360, language="lang_zh-TW", country="countryTW")

# Display the results
if search_results:
    display_results(search_results)
else:
    print("No results found.")
