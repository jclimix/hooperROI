import requests
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata
import chardet
import time

def download_player_ids(season):

    URL = f"https://www.basketball-reference.com/leagues/NBA_{season}_per_game.html"
    response = requests.get(URL)
    raw_content = response.content

    # detect encoding then decode
    detected_encoding = chardet.detect(raw_content)["encoding"]
    print(f"Detected encoding: {detected_encoding}")

    soup = BeautifulSoup(raw_content.decode(detected_encoding, errors='replace'), 'html.parser')

    # find the table by ID
    table = soup.find("table", {"id": "per_game_stats"})

    # pull player names and IDs
    players = []
    for row in table.find("tbody").find_all("tr", class_=lambda x: x != "thead"):
        player_cell = row.find("td", {"data-stat": "name_display"})
        if player_cell:
            link = player_cell.find("a")
            if link:
                player_name = link.text.strip()
                detected_unicode = [char for char in player_name if ord(char) > 127]
                if detected_unicode:
                    print(f"Detected Unicode characters in '{player_name}': {detected_unicode}")
                # normalize and remove accent marks
                player_name = unicodedata.normalize('NFKD', player_name).encode('ASCII', 'ignore').decode('utf-8')
                player_id = link["href"].split("/")[-1].replace(".html", "")
                players.append((player_name, player_id))

    df = pd.DataFrame(players, columns=["Player Name", "Player ID"])

    df = df.drop_duplicates(keep='last')

    print(df)
    df.to_csv(f'static/data/{season}_player_data.csv', index=False)

if __name__ == "__main__":
    seasons = range(2016, 2026)
    for season in seasons:
        download_player_ids(str(season))
        print(f"Download completed for {season}.")
        time.sleep(10)