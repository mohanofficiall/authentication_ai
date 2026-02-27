import requests
query = "gravity"
search_url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "format": "json",
    "list": "search",
    "srsearch": query,
    "utf8": 1,
}
r = requests.get(search_url, params=params)
print(r.json())
