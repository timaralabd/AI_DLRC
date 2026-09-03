import requests
import json
import zipfile
from pathlib import Path

print("AI-DLRC Damage Data Collector")
print("=" * 60)

# Copernicus EMS official public API
API_URL = (
    "https://rapidmapping.emergency.copernicus.eu/"
    "backend/dashboard-api/public-activations/?code=EMSR648"
)

DATA_DIR = Path("data/damage")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Connecting to Copernicus EMS API...")
print("Activation: EMSR648")
print()

# ---------------------------------------------------------
# 1. Get activation information
# ---------------------------------------------------------

response = requests.get(API_URL, timeout=60)
response.raise_for_status()

activation_data = response.json()

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

    if isinstance(obj, dict):

        for key, value in obj.items():

            if isinstance(value, str):

                value_lower = value.lower()

                if value.startswith("http"):
                    if (
                        ".zip" in value_lower
                        or ".gpkg" in value_lower
                        or ".geojson" in value_lower
                        or ".json" in value_lower
                    ):
                        if value not in download_urls:
                            download_urls.append(value)

            else:
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