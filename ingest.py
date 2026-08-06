import json
import os
from bs4 import BeautifulSoup
import pdfplumber
import requests

BASE_DIR = "./rag"
JSON_FILE = "links.json"

# Mimic a realistic browser user agent to minimize blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def scrape_html_page(url):
  """Fallback scraper for plain web pages (like ExRx or HTML articles)."""
  try:
    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")

      # Remove unwanted tags like scripts, styles, footers, navigation
      for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()

      # Extract main body text
      text = soup.get_text(separator="\n", strip=True)
      return text
    else:
      return None
  except Exception:
    return None


def extract_pdf(pdf_path):
  """Safely extract text from a downloaded PDF file."""
  full_text = ""
  try:
    with pdfplumber.open(pdf_path) as pdf:
      for page_num, page in enumerate(pdf.pages):
        text = page.extract_text(layout=False)
        if text:
          full_text += f"\n--- Page {page_num + 1} ---\n" + text + "\n"
    return full_text
  except Exception:
    return None


def process_links():
  if not os.path.exists(JSON_FILE):
    print(f"[ERROR] {JSON_FILE} not found.")
    return

  with open(JSON_FILE, "r", encoding="utf-8") as f:
    tasks = json.load(f)

  print(f"[INFO] Processing {len(tasks)} target links safely...")

  # Keep track of skipped or failed links
  skipped_items = []

  for item in tasks:
    url = item["url"]
    category = item["category"]
    name = item["name"]

    target_dir = os.path.join(BASE_DIR, category)
    os.makedirs(target_dir, exist_ok=True)
    output_txt = os.path.join(target_dir, f"{name}.txt")

    # Skip Google search URLs explicitly
    if "google.com/search" in url:
      print(f"[SKIPPED] Google search wrapper: {name}")
      skipped_items.append({"name": name, "url": url, "reason": "Google Search URL wrapper"})
      continue

    print(f"\n[PROCESSING] {name} ({category})")
    extracted_text = None
    temp_file = f"temp_{name}.file"

    try:
      response = requests.get(url, headers=HEADERS, timeout=25, stream=True)

      if response.status_code != 200:
        print(f"[FAILED] HTTP Error status {response.status_code} for URL: {url}")
        skipped_items.append({"name": name, "url": url, "reason": f"HTTP Status {response.status_code}"})
        continue

      # Check content type or URL structure to see if it's a PDF
      content_type = response.headers.get("Content-Type", "").lower()
      is_pdf_url = url.endswith(".pdf") or "pdf" in content_type

      if is_pdf_url:
        # Save stream to temporary file
        with open(temp_file, "wb") as f:
          for chunk in response.iter_content(chunk_size=8192):
            if chunk:
              f.write(chunk)

        # Verify it's actually a valid PDF file
        with open(temp_file, "rb") as f:
          header_bytes = f.read(4)

        if header_bytes.startswith(b"%PDF"):
          extracted_text = extract_pdf(temp_file)
        else:
          print(f"[WARNING] Claims to be PDF but lacks signature. Using HTML parser.")
          extracted_text = scrape_html_page(url)
      else:
        # Treat as a regular HTML web page article
        extracted_text = scrape_html_page(url)

      # Save to text file if extraction succeeded
      if extracted_text and len(extracted_text.strip()) > 100:
        with open(output_txt, "w", encoding="utf-8") as out:
          out.write(extracted_text)
        print(f"[SUCCESS] Saved clean text -> {category}/{name}.txt")
      else:
        print(f"[SKIPPED] Extracted text was empty or too short for: {name}")
        skipped_items.append({"name": name, "url": url, "reason": "Empty or insufficient extracted text content"})

    except Exception as e:
      print(f"[ERROR] Failed processing {name}: {e}")
      skipped_items.append({"name": name, "url": url, "reason": str(e)})

    finally:
      if os.path.exists(temp_file):
        os.remove(temp_file)

  # PRINT FINAL SKIPPED REPORT SUMMARY
  print("\n" + "="*50)
  print(f"BATCH PROCESSING COMPLETE. TOTAL SKIPPED/FAILED: {len(skipped_items)}")
  print("="*50)
  for idx, skip in enumerate(skipped_items, 1):
    print(f"{idx}. Name: {skip['name']}")
    print(f"   URL:  {skip['url']}")
    print(f"   Reason: {skip['reason']}")
    print("-" * 50)


if __name__ == "__main__":
  process_links()