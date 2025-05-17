import requests
import re
from bs4 import BeautifulSoup

API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def fetch_events_via_api(year: int, max_events: int = 20) -> list[str]:
    # 1) Retrieve the list of sections on the page
    sec_params = {
        "action": "parse",
        "page": str(year),
        "prop": "sections",
        "format": "json",
        "formatversion": 2
    }
    sec_resp = requests.get(API_URL, params=sec_params, headers=HEADERS)
    sec_data = sec_resp.json().get("parse", {})
    sections = sec_data.get("sections", [])
    idx = next((s["index"] for s in sections if s.get("line") == "Events"), None)
    if not idx:
        print(f"[!] No 'Events' section found in API for {year}")
        return []

    # 2) Fetch only that section’s HTML
    text_params = {
        "action": "parse",
        "page": str(year),
        "section": idx,
        "prop": "text",
        "format": "json",
        "formatversion": 2
    }
    text_resp = requests.get(API_URL, params=text_params, headers=HEADERS)
    html = text_resp.json().get("parse", {}).get("text", "")
    if not html:
        print(f"[!] API returned empty HTML for Events section of {year}")
        return []

    # 3) Parse and iterate through all top-level <ul> blocks
    soup = BeautifulSoup(html, "html.parser")
    # find all ULs that are not nested inside another UL
    top_uls = [ul for ul in soup.find_all("ul") if not ul.find_parent("ul")]
    if not top_uls:
        print(f"[!] No top-level <ul> found in Events section HTML for {year}")
        return []

    events = []
    for ul in top_uls:
        for li in ul.find_all("li", recursive=False):
            # strip bracketed references and filter by length
            text = re.sub(r"\[\d+\]", "", li.get_text(" ", strip=True))
            if len(text.split()) >= 6:
                events.append(text)
                if len(events) >= max_events:
                    return events

    if not events:
        print(f"[!] No events found for {year} in any month")
    return events

if __name__ == "__main__":
    year = 2019
    evts = fetch_events_via_api(year)
    print(f"\nTop Events from {year} (via API):\n")
    for i, e in enumerate(evts, 1):
        print(f"{i}. {e}")

# Todo: 
    #Implement the following function to attempt some heuristic bullshit
'''
def is_significant_event(event_text: str) -> bool:
    keywords = [
        "list of words", "pandemic", "death", "dies", 
        "first", "king", "queen", "president", "leader", 
        "dictator", "mass", "murder", "crisis", "earthquake", 
        ]
    return any(word in event_text.lower() for word in keywords) and len(event_text.spli() >=8)    
'''
    # Can do this with spaCy too for some NLP but that might require more work... something like this:
'''
import spacy
nlp = spacy.load("en_core_web_sm")

def get_event_score(text):
    doc = nlp(text)
    entity_count = len([ent for ent in doc.ents if ent.label_ in ("GPE", "ORG", "PERSON")])
    verb_count = len([token for token in doc if token.pos_ == "VERB"])
    return entity_count + verb_count

# Example use
scored_events = sorted(events, key=get_event_score, reverse=True)
'''