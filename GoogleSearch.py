import requests
import os
import csv
from urllib.parse import urlparse, unquote, parse_qs
from dotenv import load_dotenv
import subprocess  # For executing Markitdown command

# Load environment variables
load_dotenv()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CSE_ID = os.getenv("GOOGLE_SEARCH_CSE_ID")
os.environ["PYTHONIOENCODING"] = "utf-8"

def google_search(api_key, cse_id, query, num_results=10, max_results=500, last_days=180, language="lang_zh-TW", country="countryTW"):
    """
    Perform a Google Custom Search using the Custom Search JSON API.

    Args:
        api_key (str): Your Google API key.
        cse_id (str): Your Custom Search Engine ID.
        query (str): The search query.
        num_results (int): Number of results per request (max is 10).
        max_results (int): Maximum total results to retrieve (default is 500).
        last_days (int): Number of days to restrict the search to recent results.
        language (str): Language filter.
        country (str): Country restriction.

    Returns:
        list: A list of search results.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    results = []
    date_limit = f"d{last_days}"

    for start in range(1, max_results + 1, num_results):
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num_results,
            "start": start,
            "dateRestrict": date_limit,
            "sort": "date",
            "lr": language,
            "cr": country
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

def save_results_to_csv(results, filename="GoogleResults.csv"):
    """
    Save search results to a CSV file.

    Args:
        results (list): A list of search result items.
        filename (str): Name of the output CSV file.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Title", "Link", "Snippet", "File", "MD File"])
        writer.writeheader()
        for item in results:
            writer.writerow({
                "Title": item.get("title"),
                "Link": item.get("link"),
                "Snippet": item.get("snippet"),
                "File": "",
                "MD File": ""
            })

def download_files_from_links_and_convert(csv_filename="GoogleResults.csv"):
    """
    Download files from links in the CSV, convert PDFs to Markdown, and update the "File" and "MD File" columns.

    Args:
        csv_filename (str): Name of the input/output CSV file.
    """
    with open(csv_filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    total_rows = len(rows)
    print(f"Total rows to process: {total_rows}")

    pdf_counter = 1

    for index, row in enumerate(rows):
        link = row["Link"]
        if link:
            try:
                # Decode the URL to handle redirects and special characters
                decoded_link = unquote(link)
                if decoded_link.lower().endswith(".pdf") or "fileredirect.aspx" in decoded_link:
                    response = requests.get(link, stream=True, allow_redirects=True)
                    if response.status_code == 200:
                        # Handle redirected URLs to extract actual file path
                        final_url = response.url
                        parsed_url = urlparse(final_url)
                        if "fileredirect.aspx" in parsed_url.path:
                            query_params = parse_qs(parsed_url.query)
                            if "Path" in query_params:
                                clean_path = unquote(query_params["Path"][0])
                                filename = os.path.basename(clean_path)
                                filepath = os.path.join("PDF", filename)
                                os.makedirs("PDF", exist_ok=True)
                            else:
                                filepath = os.path.join("PDF", f"pdf{pdf_counter}.pdf")
                                pdf_counter += 1
                        else:
                            filename = os.path.basename(parsed_url.path) or f"pdf{pdf_counter}.pdf"
                            filepath = os.path.join("PDF", filename)
                            os.makedirs("PDF", exist_ok=True)
                            pdf_counter += 1

                        with open(filepath, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        row["File"] = filepath

                        # Convert the PDF to Markdown using Markitdown
                        md_filepath = os.path.join("MD", os.path.basename(filepath).replace(".pdf", ".md"))
                        os.makedirs("MD", exist_ok=True)
                        try:
                            with open(md_filepath, "w", encoding="utf-8") as md_file:
                                subprocess.run([
                                    "markitdown", filepath
                                ], stdout=md_file, check=True)
                            row["MD File"] = md_filepath
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting {filepath} to Markdown: {e}")
                            row["MD File"] = ""
                    else:
                        print(f"Failed to download {link}: {response.status_code}")
                else:
                    print(f"Skipped non-PDF link: {link}")
                    row["File"] = ""
                    row["MD File"] = ""
            except Exception as e:
                print(f"Error processing {link}: {e}")

        print(f"Processed row {index + 1} of {total_rows}")

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Title", "Link", "Snippet", "File", "MD File"])
        writer.writeheader()
        writer.writerows(rows)

# Example usage
QUERY = "得標統計表 T004 -公司債 filetype:pdf"
search_results = google_search(GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CSE_ID, QUERY, max_results=500, last_days=360)
if search_results:
    save_results_to_csv(search_results)
    download_files_from_links_and_convert()
