import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/2019"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

print("== All <h2> Sections on Page ==")
for h2 in soup.find_all("h2"):
    print(f"[RAW H2]: {h2}")