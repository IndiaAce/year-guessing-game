import requests
import re
import random
from bs4 import BeautifulSoup

def is_significant_event(event_text: str) -> bool:
    keywords = [
        "pandemic", "death", "dies",
        "first", "king", "queen", "president", "leader",
        "dictator", "mass", "murder", "crisis", "earthquake",
        "election", "vote", "battle", "war", "treaty", "revolution",
        "independence", "constitution", "launch", "discovery", "invent",
        "landing", "protest", "strike", "riot", "assassination",
        "flood", "hurricane", "tsunami", "volcano", "stock", "inflation"
    ]
    return any(word in event_text.lower() for word in keywords) and len(event_text.split()) >= 8

def obfuscate_year(event_text: str, year: int) -> str:
    # replace exact year occurrences with 'XXXX'
    pattern = r'\b' + re.escape(str(year)) + r'\b'
    return re.sub(pattern, 'XXXX', event_text)

API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def fetch_events_via_api(year: int, max_events: int = 4) -> list[str]:
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

def gameplay_loop(events: list[str], year: int, attempts: int = 3) -> None:
    print("\nGuess the year for the following events:\n")
    for i, event in enumerate(events, 1):
        obf = obfuscate_year(event, year)
        print(f"{i}. {obf}")
    for attempt in range(1, attempts + 1):
        guess = input(f"\nAttempt {attempt}/{attempts} - Your guess: ")
        try:
            if int(guess) == year:
                print("You nailed it!")
                return
        except ValueError:
            print("Please enter a valid number.")
            continue
        print("Wrong guess.")
    print(f"\nOut of attempts! The year was {year}.")

if __name__ == "__main__":
    year_choice = [2025, 2019, 2016, 2012, 2001, 2000, 1980, 1964, 1934, 1914, 1913, 1912, 1812]
    year = random.choice(year_choice)
    # fetch a larger batch and filter for significant events
    raw_events = fetch_events_via_api(year, max_events=100)
    sig_events = [e for e in raw_events if is_significant_event(e)]
    # if not enough, fetch more and retry
    if len(sig_events) < 4:
        print(f"[!] Only {len(sig_events)} significant events found for {year}, fetching more.")
        raw_events = fetch_events_via_api(year, max_events=200)
        sig_events = [e for e in raw_events if is_significant_event(e)]
    # ensure at least 4 events
    if len(sig_events) < 4:
        raise ValueError(f"Not enough significant events found for year {year}")
    # pick 4 random significant events
    events = random.sample(sig_events, 4)
    gameplay_loop(events, year)