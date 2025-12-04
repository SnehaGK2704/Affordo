from flask import Flask, render_template, request
from dotenv import load_dotenv
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
import os, re
from urllib.parse import urlparse, parse_qs, unquote

load_dotenv()
SERP_KEY = os.getenv("SERPAPI_KEY")

app = Flask(__name__)


# --------------------------------------------------
# Helper: convert "₹21,999" → 21999
# --------------------------------------------------
def price_to_number(text):
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


# --------------------------------------------------
# Extract clean product name from link
# --------------------------------------------------
def extract_name_from_url(url):
    """
    Cleans Amazon/Flipkart URLs → returns a good search name.
    """
    url_dec = unquote(url.lower())

    # AMAZON
    if "amazon." in url_dec:
        # Prefer slug before /dp/
        m = re.search(r"amazon\.[^/]+/([^/]+)/dp", url_dec)
        if m:
            words = m.group(1).replace("-", " ").split()
            return " ".join(words[:5])

        # fallback to dp id
        m2 = re.search(r"/dp/([A-Z0-9]{6,})", url_dec)
        if m2:
            return m2.group(1)

    # FLIPKART
    if "flipkart.com" in url_dec:
        # 1) Try ?pid=
        parsed = urlparse(url_dec)
        qs = parse_qs(parsed.query)
        if "pid" in qs and qs["pid"]:
            return qs["pid"][0]  # Flipkart Product ID

        # 2) Try slug after /p/
        m = re.search(r"/p/([^/?]+)", url_dec)
        if m:
            words = m.group(1).replace("-", " ").split()
            return " ".join(words[:5])

        # 3) fallback slug
        m2 = re.search(r"flipkart\.com/[^/]+/([^/?]+)", url_dec)
        if m2:
            words = m2.group(1).replace("-", " ").split()
            return " ".join(words[:5])

    # Final fallback: take readable words
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", " ", url_dec)
    words = cleaned.split()
    return " ".join(words[:5])


# --------------------------------------------------
# AMAZON SCRAPER (Playwright) — SUPER ACCURATE
# --------------------------------------------------
def fetch_amazon(product_name_or_url):
    """
    Final stable Amazon scraper:
    - Name search via SerpAPI
    - Direct product link scraping via Playwright
    - Handles ALL Amazon price formats
    """

    # -----------------------------
    # Resolve URL
    # -----------------------------
    if product_name_or_url.startswith("http"):
        product_url = product_name_or_url
    else:
        params = {
            "engine": "google",
            "api_key": SERP_KEY,
            "q": f"{product_name_or_url} site:amazon.in"
        }
        result = GoogleSearch(params).get_dict()
        organic = result.get("organic_results", [])
        if not organic:
            return {"error": "Amazon product not found"}
        product_url = organic[0].get("link")

    # -----------------------------
    # Scrape Amazon page
    # -----------------------------
    def fetch_amazon(product_name_or_url):

    # Decide URL
        if product_name_or_url.startswith("http"):
            product_url = product_name_or_url
        else:
            params = {
            "engine": "google",
            "api_key": SERP_KEY,
            "q": f"{product_name_or_url} site:amazon.in"
        }
        result = GoogleSearch(params).get_dict()
        organic = result.get("organic_results", [])
        if not organic:
            return {"error": "Amazon product not found in search results"}
        product_url = organic[0].get("link")

    # Scrape using Playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(product_url, timeout=60000)

            # TITLE
            title = "Unknown Product"
            if page.locator("span#productTitle").count() > 0:
                title = page.locator("span#productTitle").first.inner_text().strip()

            # PRICE (only whole number)
            price = None

            # 1) Try full ₹xx,xxx from a-offscreen
            if page.locator("span.a-price span.a-offscreen").count() > 0:
                raw = page.locator("span.a-price span.a-offscreen").first.inner_text().strip()

                # Extract only whole part using regex
                m = re.search(r"₹\s?([\d,]+)", raw)
                if m:
                    whole = m.group(1)
                    price = f"₹{whole}"

            # 2) Try whole part manually
            if not price:
                if page.locator("span.a-price-whole").count() > 0:
                    whole = page.locator("span.a-price-whole").first.inner_text().strip()
                    whole_clean = re.sub(r"[^\d]", "", whole)
                    price_int = int(whole_clean)
                    price = f"₹{price_int:,}"

            # If still missing
            if not price:
                price = "—"

            browser.close()

            return {
                "title": title,
                "rating": None,
                "product_link": product_url,
                "variants": [],
                "best_variant": None,
                "price_raw": price,
                "price_numeric": price_to_number(price),
            }

    except Exception as e:
        return {"error": f"Amazon scraping failed: {e}"}





# --------------------------------------------------
# FLIPKART SCRAPER (via SerpAPI - Safe)
# --------------------------------------------------
def fetch_flipkart(product_name_or_id):
    """
    Uses SerpAPI Google engine to fetch Flipkart price safely.
    """

    query = product_name_or_id
    params = {
        "engine": "google",
        "api_key": SERP_KEY,
        "q": f"{query} site:flipkart.com"
    }

    result = GoogleSearch(params).get_dict()

    organic = result.get("organic_results", [])
    if not organic:
        return {"error": "No Flipkart results found"}

    item = organic[0]
    title = item.get("title")
    link = item.get("link")

    snippet = item.get("snippet", "")
    price_match = re.search(r"₹[\d,]+", snippet)
    price_raw = price_match.group(0) if price_match else None

    return {
        "title": title,
        "rating": None,
        "product_link": link,
        "variants": [],
        "best_variant": None,
        "price_raw": price_raw,
        "price_numeric": price_to_number(price_raw)
    }


# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/results")
def results():
    query = request.args.get("query", "").strip()

    # Convert URL → name if needed
    if query.startswith("http"):
        product_name = extract_name_from_url(query)
    else:
        product_name = query

    results = {
        "Amazon": fetch_amazon(product_name),
        "Flipkart": fetch_flipkart(product_name)
    }

    # Best deal
    best = None
    for platform, data in results.items():
        if data and data.get("price_numeric"):
            if best is None or data["price_numeric"] < best["price_numeric"]:
                best = {
                    "platform": platform,
                    "price_numeric": data["price_numeric"]
                }

    return render_template("results.html",
                           query=product_name,
                           results=results,
                           best=best)


if __name__ == "__main__":
    app.run(debug=True)
