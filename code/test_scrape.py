import requests
import re
import random
from bs4 import BeautifulSoup

def display_board(events, event_year_map, ungrouped_ids, year_letters):
    print("\nGroup the 16 events into the correct years:\n")
    for i in sorted(ungrouped_ids):
        ev = events[i-1]
        obf = obfuscate_year(ev, event_year_map[i])
        print(f"{i}. {obf}")
    print("\nYears:")
    for letter, y in year_letters.items():
        print(f"{letter}) {y}")
    print()

def connections_game(year_choices):
    import random
    # pick 4 distinct years
    years = random.sample(year_choices, 4)
    # fetch events per year
    events_by_year = {}
    for y in years:
        raw = fetch_events_via_api(y, max_events=50)
        sig = [e for e in raw if is_significant_event(e)]
        if len(sig) < 4:
            raw = fetch_events_via_api(y, max_events=100)
            sig = [e for e in raw if is_significant_event(e)]
        if len(sig) < 4:
            raise ValueError(f"Not enough significant events for year {y}")
        events_by_year[y] = random.sample(sig, 4)
    # flatten and map ids
    events_flat = []
    event_year_map = {}
    for y in years:
        for ev in events_by_year[y]:
            idx = len(events_flat) + 1
            events_flat.append(ev)
            event_year_map[idx] = y
    # setup game state
    ungrouped = set(range(1, len(events_flat) + 1))
    letters = dict(zip(["A", "B", "C", "D"], years))
    groups_done = 0
    total_groups = 4
    # main loop
    while groups_done < total_groups:
        display_board(events_flat, event_year_map, ungrouped, letters)
        inp = input("Enter 4 event numbers and a year letter (e.g. '3 7 12 15 A'): ")
        parts = inp.strip().split()
        if len(parts) != 5:
            print("Invalid input format.")
            continue
        *num_strs, let = parts
        try:
            ids = [int(n) for n in num_strs]
        except ValueError:
            print("Event IDs must be numbers.")
            continue
        let = let.upper()
        if let not in letters:
            print("Invalid year letter. Choose A-D.")
            continue
        chosen_year = letters[let]
        # validate group
        if any(i not in ungrouped for i in ids):
            print("One or more event IDs already grouped or invalid.")
            continue
        if all(event_year_map[i] == chosen_year for i in ids):
            groups_done += 1
            for i in ids:
                ungrouped.remove(i)
            print(f"Correct! {total_groups - groups_done} groups to go.")
        else:
            correct = sum(1 for i in ids if event_year_map[i] == chosen_year)
            print(f"{correct}/4 correct. Try again.")
    print("Congratulations! You've grouped all events!")

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

if __name__ == "__main__":
    year_choice = [2025, 2019, 2016, 2012, 2001, 2000, 1980, 1964, 1934, 1914, 1913, 1912, 1812]
    connections_game(year_choice)