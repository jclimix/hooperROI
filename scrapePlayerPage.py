import requests
from bs4 import BeautifulSoup, Comment, MarkupResemblesLocatorWarning
import pandas as pd
import chardet
import warnings
from loguru import logger

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

logger.add("player_scraper.log", rotation="10MB", level="INFO")

def get_player_id(year, player_name):
    try:
        df = pd.read_csv(f"static/data/{year}_player_data.csv")
        player_row = df[df["Player Name"].str.lower() == player_name.lower()]
        if not player_row.empty:
            return player_row["Player ID"].values[0]
        else:
            logger.warning(f"Player not found: {player_name} for {year}")
            return "Player not found"
    except Exception as e:
        logger.error(f"Error in get_player_id: {e}")
        return "Player not found"

def scrape_html(player_id):
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to retrieve page for {player_id}. Status code: {response.status_code}")
            return None

        raw_content = response.content
        detected_encoding = chardet.detect(raw_content)["encoding"]
        soup = BeautifulSoup(raw_content.decode(detected_encoding, errors='replace'), 'html.parser')
        return soup
    except Exception as e:
        logger.error(f"Error in scrape_html: {e}")
        return None

def get_player_headshot(soup, player_id: str) -> str:
    try:
        for div in soup.find_all('div'):
            img = div.find('img', src=True)
            if img and 'headshots' in img['src'] and player_id in img['src']:
                return img['src']
        logger.warning(f"No headshot found for player {player_id}, using fallback image.")
        return "static/images/headshot_fallback.png"  # fallback image
    except Exception as e:
        logger.error(f"Error in get_player_headshot: {e}")
        return "static/images/headshot_fallback.png"  # fallback image on error


def scrape_html_table(soup, table_id):
    if not soup:
        return None
    try:
        for div in soup.find_all("div"):
            table = div.find("table", id=lambda x: x and x.startswith(table_id))
            if table:
                return table  

        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(str(comment), "html.parser")
            table = comment_soup.find("table", id=lambda x: x and x.startswith(table_id))
            if table:
                return table 

        logger.warning(f"Table with id starting with '{table_id}' not found.")
        return None
    except Exception as e:
        logger.error(f"Error in scrape_html_table: {e}")
        return None

def html_table_to_df_stats(table):
    if table is None:
        logger.warning("Table not found.")
        return None
    try:
        headers = [header.text.strip() for header in table.find_all("th")]
        
        rows = []
        for row in table.find("tbody").find_all("tr"):
            cells = [cell.text.strip() for cell in row.find_all(["th", "td"])]
            if len(cells) < len(headers):
                cells += [""] * (len(headers) - len(cells)) 
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]
            rows.append(cells)

        min_cols = min(len(headers), len(rows[0]) if rows else len(headers))
        headers = headers[:min_cols]
        rows = [row[:min_cols] for row in rows]

        df = pd.DataFrame(rows, columns=headers)
        return df
    except Exception as e:
        logger.error(f"Error in html_table_to_df_stats: {e}")
        return None

def convert_nba_season_to_year(season):
    try:
        start_year, end_year_suffix = season.split("-")
        end_year = int(start_year[:2] + end_year_suffix)
        return end_year
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid season format: {season}. Error: {e}")
        return None

def rearrange_base_stats_df(df):
    desired_columns = [
        "Season", "Age", "Team", "G", "MP", "PTS", "AST", "TRB", 
        "BLK", "STL", "FG%", "eFG%", "2P%", "3P%", "FT%"
    ]
    return df[[col for col in desired_columns if col in df.columns]].reset_index(drop=True)

def rearrange_adv_stats_df(df):
    desired_columns = [
        "Season", "Age", "Team", "G", "PER", "WS", "TS%", 
        "BPM", "VORP", "TRB%", "AST%", "STL%"
    ]
    return df[[col for col in desired_columns if col in df.columns]].reset_index(drop=True)

def clean_duplicate_columns(df):
    return df.loc[:, ~df.columns.duplicated(keep='first')]

if __name__ == '__main__':
    player_name = "Nikola Jokic"
    season = "2024-25"
    year = convert_nba_season_to_year(season)

    player_id = get_player_id(year, player_name)
    soup_data = scrape_html(player_id)

    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"

    player_headshot = get_player_headshot(soup_data, player_id)

    pergame_table = scrape_html_table(soup_data, table_id="per_game_stats")
    pergame_table_df = html_table_to_df_stats(pergame_table)

    try:
        age = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Age'].values[0]
        position = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Pos'].values[0]
        team = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Team'].values[0]
    except:
        age, position, team = "N/A", "N/A", "N/A"

    pergame_table_df = rearrange_base_stats_df(pergame_table_df)

    adv_table = scrape_html_table(soup_data, table_id="advanced")
    adv_table_df = html_table_to_df_stats(adv_table)
    adv_table_df = rearrange_adv_stats_df(adv_table_df)

    logger.info(f"URL: {url}")
    logger.info(f"Player: {player_name} ({player_id})")
    logger.info(f"Headshot: {player_headshot}")
    logger.info(f"Age: {age}")
    logger.info(f"Position: {position}")
    logger.info(f"Team: {team}")
    logger.info(f"Base Stats:\n{pergame_table_df}")
    logger.info(f"Advanced Stats:\n{adv_table_df}")
