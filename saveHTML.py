import requests

def save_html(url, filename):
    """Scrapes the HTML from a URL and saves it to a file."""
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"HTML saved successfully to {filename}")
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

url = "https://www.basketball-reference.com/players/j/jokicni01.html"  
filename = "player_page.html"

save_html(url, filename)
