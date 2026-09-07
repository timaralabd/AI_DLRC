import requests
import json
import re
import zipfile
from pathlib import Path
from html.parser import HTMLParser

print("AI-DLRC Damage Data Collector")
print("=" * 60)

# Copernicus EMS official public API
API_URL = (
    "https://rapidmapping.emergency.copernicus.eu/"
    "backend/dashboard-api/public-activations/?code=EMSR648"
)
ACTIVATION_PAGE_URL = "https://mapping.emergency.copernicus.eu/activations/EMSR648"

DATA_DIR = Path("data/damage")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Connecting to Copernicus EMS API...")
print("Activation: EMSR648")
print()


class DownloadLinkParser(HTMLParser):
    """Collect downloadable product links from the public activation page."""

    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        href = "".join(dict(attrs).get("href", "").split())
        href_lower = href.lower()
        if href.startswith("http") and (".zip" in href_lower or ".gpkg" in href_lower):
            if href not in self.urls:
                self.urls.append(href)

# ---------------------------------------------------------
# 1. Get activation information
# ---------------------------------------------------------

try:
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()
    activation_data = response.json()
except requests.HTTPError as error:
    if response.status_code not in (401, 403):
        raise

    print(f"Dashboard API unavailable ({response.status_code}); using public activation page.")
    page_response = requests.get(ACTIVATION_PAGE_URL, timeout=60)
    page_response.raise_for_status()
    page_html = "".join(page_response.text.split())
    page_parser = DownloadLinkParser()
    page_parser.feed(page_html)
    page_urls = re.findall(r'https://[^"\'<>]+\.(?:zip|gpkg)', page_html, re.IGNORECASE)
    activation_data = {
        "activation_page": ACTIVATION_PAGE_URL,
        "download_urls": list(dict.fromkeys(page_parser.urls + page_urls)),
        "api_error": str(error),
    }

print("Copernicus API connection successful!")
print()

# Save the original API response
metadata_file = DATA_DIR / "EMSR648_metadata.json"

with open(metadata_file, "w", encoding="utf-8") as file:
    json.dump(
        activation_data,
        file,
        indent=2,
        ensure_ascii=False
    )

print(f"Metadata saved to:")
print(metadata_file)
print()

# ---------------------------------------------------------
# 2. Find downloadable files inside API response
# ---------------------------------------------------------

download_urls = []


def search_urls(obj):
    """
    Recursively search the API response
    for downloadable URLs.
    """

    if isinstance(obj, str):
        value_lower = obj.lower()
        if obj.startswith("http") and (
            ".zip" in value_lower or ".gpkg" in value_lower
        ):
            if obj not in download_urls:
                download_urls.append(obj)

    elif isinstance(obj, dict):

        for key, value in obj.items():

            search_urls(value)

    elif isinstance(obj, list):

        for item in obj:
            search_urls(item)


search_urls(activation_data)

print("Downloadable files found:")
print("-" * 60)

for index, url in enumerate(download_urls, start=1):
    print(f"{index}. {url}")

print()

# ---------------------------------------------------------
# 3. Download Vector Package
# ---------------------------------------------------------

vector_urls = [
    url for url in download_urls
    if ".zip" in url.lower() or ".gpkg" in url.lower()
]

if not vector_urls:

    print("No direct Vector Package URL was found.")
    print()
    print("The API response was saved here:")
    print(metadata_file)
    print()
    print("We will inspect the API structure before downloading.")
    raise SystemExit


# Download the first available vector package
selected_url = vector_urls[0]

print("Selected Vector Package:")
print(selected_url)
print()

file_name = selected_url.split("/")[-1].split("?")[0]

if not file_name:
    file_name = "EMSR648_vector_package.zip"

output_file = DATA_DIR / file_name

print("Downloading real damage data...")

download_response = requests.get(
    selected_url,
    timeout=180
)

download_response.raise_for_status()

with open(output_file, "wb") as file:
    file.write(download_response.content)

print()
print("Download completed!")
print(f"Saved to:")
print(output_file)
print()

# ---------------------------------------------------------
# 4. Extract ZIP
# ---------------------------------------------------------

if output_file.suffix.lower() == ".zip":

    extract_dir = DATA_DIR / "extracted"
    extract_dir.mkdir(exist_ok=True)

    print("Extracting Vector Package...")

    with zipfile.ZipFile(output_file, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print("Extraction completed!")
    print()

    print("Extracted files:")
    print("-" * 60)

    files = list(extract_dir.rglob("*"))

    file_count = 0

    for file in files:

        if file.is_file():

            print(file)
            file_count += 1

    print()
    print(f"Total extracted files: {file_count}")

print()
print("=" * 60)
print("AI-DLRC damage data collection completed!")
print("=" * 60)