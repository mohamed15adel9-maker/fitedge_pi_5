import json
import os
from bs4 import BeautifulSoup
import pdfplumber
import requests

BASE_DIR = "./rag"
JSON_FILE = "links.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
}

# If any of these appear, the "text" is really a bot-block / CAPTCHA page.
BLOCK_MARKERS = [
    "checking your browser",
    "recaptcha",
    "enable javascript",
    "are you a robot",
    "cloudflare",
    "access denied",
]


def is_block_page(text):
    if not text:
        return False
    low = text.lower()
    return any(m in low for m in BLOCK_MARKERS)


def scrape_html_page(url):
    """Extract readable text from an HTML article."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.extract()
            return soup.get_text(separator="\n", strip=True)
        return None
    except Exception:
        return None


def extract_pdf(pdf_path):
    """Extract text from a downloaded PDF file, page by page."""
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text(layout=False)
                if text:
                    full_text += f"\n--- Page {page_num + 1} ---\n" + text + "\n"
        return full_text
    except Exception as e:
        print(f"    [pdf extract error] {e}")
        return None


def process_links():
    if not os.path.exists(JSON_FILE):
        print(f"[ERROR] {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    print(f"[INFO] Processing {len(tasks)} links...")
    skipped_items = []

    for item in tasks:
        url = item["url"]
        category = item["category"]
        name = item["name"]

        target_dir = os.path.join(BASE_DIR, category)
        os.makedirs(target_dir, exist_ok=True)
        output_txt = os.path.join(target_dir, f"{name}.txt")

        # Re-check cached files: skip only if they exist AND aren't junk.
        if os.path.exists(output_txt) and os.path.getsize(output_txt) > 100:
            existing = open(output_txt, encoding="utf-8", errors="ignore").read()
            if not is_block_page(existing):
                print(f"[CACHED] {name}")
                continue
            else:
                print(f"[RE-DOING] {name} (cached file was a block page)")
                os.remove(output_txt)

        if "google.com/search" in url:
            skipped_items.append({"name": name, "url": url, "reason": "Google search URL"})
            continue

        print(f"\n[PROCESSING] {name} ({category})")
        extracted_text = None
        temp_file = f"temp_{name}.file"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
            if response.status_code != 200:
                print(f"[FAILED] HTTP {response.status_code}")
                skipped_items.append({"name": name, "url": url, "reason": f"HTTP {response.status_code}"})
                continue

            content_type = response.headers.get("Content-Type", "").lower()
            is_pdf = url.lower().endswith(".pdf") or "pdf" in content_type

            if is_pdf:
                with open(temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                with open(temp_file, "rb") as f:
                    header = f.read(5)
                if header.startswith(b"%PDF"):
                    extracted_text = extract_pdf(temp_file)
                else:
                    # Not actually a PDF (probably an HTML block page). Parse as HTML.
                    print("    [note] URL said PDF but file isn't a PDF; trying HTML.")
                    extracted_text = scrape_html_page(url)
            else:
                extracted_text = scrape_html_page(url)

            # Reject block pages BEFORE saving.
            if is_block_page(extracted_text):
                print(f"[SKIPPED] Block/CAPTCHA page: {name}")
                skipped_items.append({"name": name, "url": url, "reason": "Bot-block / CAPTCHA page"})
                continue

            if extracted_text and len(extracted_text.strip()) > 100:
                with open(output_txt, "w", encoding="utf-8") as out:
                    out.write(extracted_text)
                print(f"[SUCCESS] -> {category}/{name}.txt ({len(extracted_text)} chars)")
            else:
                print(f"[SKIPPED] Empty/too short: {name}")
                skipped_items.append({"name": name, "url": url, "reason": "Empty or too short"})

        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            skipped_items.append({"name": name, "url": url, "reason": str(e)})
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    print("\n" + "=" * 50)
    print(f"COMPLETE. SKIPPED/FAILED: {len(skipped_items)}")
    print("=" * 50)
    for i, s in enumerate(skipped_items, 1):
        print(f"{i}. {s['name']}\n   {s['url']}\n   {s['reason']}\n" + "-" * 40)


if __name__ == "__main__":
    process_links()
