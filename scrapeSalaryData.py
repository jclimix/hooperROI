import requests
from bs4 import BeautifulSoup, Comment, MarkupResemblesLocatorWarning
from scrapeTotalSeasonGames import *
import pandas as pd
import chardet
import warnings
from loguru import logger

logger.add("logs/salary_scraper.log", rotation="10MB", level="INFO")

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

def get_player_id(year, player_name):
    """Get the player ID from the player data CSV for a given year."""
    df = pd.read_csv(f"static/data/{year}_player_data.csv")
    player_row = df[df["Player Name"].str.lower() == player_name.lower()]
    if not player_row.empty:
        return player_row["Player ID"].values[0]
    else:
        return "Player not found"

def scrape_html(player_id):
    """Scrape HTML using given player ID in URL."""
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    
    response = requests.get(url)
    if response.status_code != 200:
        logger.error("Failed to retrieve page.")
        return None

    raw_content = response.content
    detected_encoding = chardet.detect(raw_content)["encoding"]

    soup = BeautifulSoup(raw_content.decode(detected_encoding, errors='replace'), 'html.parser')
    return soup

def scrape_html_table(soup, table_id):
    """Scrape beautifulsoup HTML response data for a table with a given ID."""
    if not soup:
        return None

    # check visible tables
    for div in soup.find_all("div"):
        table = div.find("table", id=lambda x: x and x.startswith(table_id))
        if table:
            return table  # Found directly, return it

    # fallback: find table inside comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment_soup = BeautifulSoup(str(comment), "html.parser")  # convert comment to BeautifulSoup object
        table = comment_soup.find("table", id=lambda x: x and x.startswith(table_id))
        if table:
            return table  # found inside comment, return parsed table

    logger.warning(f"Table with id starting with '{table_id}' not found.")
    return None

def scrape_html_current_salary_table(soup):
    """Scrape beautifulsoup HTML response data for a table where the ID begins with 'contracts_'."""

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    contract_table = None

    # search for contract table inside the comments
    for comment in comments:
        if 'id="contracts_' in comment:
            contract_table = BeautifulSoup(comment, 'html.parser')
            break

    return contract_table

def html_table_to_df_adv(table):
    """Return a DataFrame from a given HTML table element."""

    if table is None:
        logger.warning("Table not found.")
        return None

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

def html_table_to_df_past_salary(table):
    """Return a DataFrame from a given HTML table element."""
    if table is None:
        logger.warning("Salary table not found in HTML.")
        return None

    headers = [th.text.strip() for th in table.find("thead").find_all("th")]

    rows = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all(["th", "td"])  # includes 'th' since season is in <th>
        row_data = [col.get_text(strip=True) for col in cols]
        rows.append(row_data)

    df = pd.DataFrame(rows, columns=headers)

    return df

def html_table_to_df_current_salary(contract_table):
    """Return a DataFrame from a given HTML table element."""
    if contract_table:
        table = contract_table.find("table")
        
        if table:
            header_row = table.find("tr", {"class": "thead"})
            headers = [th.text.strip() for th in header_row.find_all("th")]

            data = []
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                row_data = [col.get_text(strip=True) for col in cols]
                data.append(row_data)

            df = pd.DataFrame(data, columns=headers)
            return df
        
def convert_nba_season_to_year(season):
    """Convert NBA season format '2014-15' to simple 4-digit year '2015'."""
    try:
        start_year, end_year_suffix = season.split("-")
        end_year = int(start_year[:2] + end_year_suffix)
        return end_year
    except (ValueError, AttributeError):
        logger.error(f"Invalid season format: {season}")
        return None
    
def money_to_float(s):
    """Convert string with $ and commas to a float variable."""
    try:
        return float(s.replace("$", "").replace(",", ""))
    except Exception as e:
        logger.error(f"Error converting money string to float: {e}")
        return 0.0

if __name__ == '__main__':
        
    player_name = "LeBron James"
    season = "2024-25"
    year = convert_nba_season_to_year(season)

    player_id = get_player_id(year, player_name)
    soup_data = scrape_html(player_id)

    adv_table = scrape_html_table(soup_data, table_id="advanced")
    adv_table_df = html_table_to_df_adv(adv_table)
    win_shares = adv_table_df.loc[adv_table_df["Season"] == season, "WS"].values[0]
    logger.info(f"Win Shares: {win_shares}")

    salary_table = scrape_html_table(soup_data, table_id="all_salaries")
    salary_table_df = html_table_to_df_past_salary(salary_table)
    if salary_table_df is not None:
        logger.info(f"Salary Table:\n{salary_table_df}")
        if season in salary_table_df["Season"].values:
            logger.info(f"Season {season} found in salary table.")
            salary = salary_table_df.loc[salary_table_df["Season"] == season, "Salary"].values[0]
            logger.info(f"Salary in float format: {money_to_float(salary)}")
        else:
            logger.warning(f"Season '{season}' not found in DataFrame.")
            salary_table = scrape_html_current_salary_table(soup_data)
            salary_table_df = html_table_to_df_current_salary(salary_table)
            salary = salary_table_df[season].iloc[0]
            logger.info(f"Salary in float format: {money_to_float(salary)}")
    else:
        logger.warning(f"Season '{season}' not found in DataFrame.")
        salary_table = scrape_html_current_salary_table(soup_data)
        salary_table_df = html_table_to_df_current_salary(salary_table)
        salary = salary_table_df[season].iloc[0]
        logger.info(f"Salary in float format: {money_to_float(salary)}")