import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
from loguru import logger
from io import StringIO

CURRENT_SEASON = "2024-25"
LEAGUE_WINS_CSV = "static/data/league_wins_teams.csv"
SALARY_CAP_CSV = "static/data/nba_salary_caps.csv"

league_wins_df = pd.read_csv(LEAGUE_WINS_CSV) if os.path.exists(LEAGUE_WINS_CSV) else None
salary_cap_df = pd.read_csv(SALARY_CAP_CSV) if os.path.exists(SALARY_CAP_CSV) else None

def convert_season_to_year(season):
    """Convert a season format (e.g., '2023-24') to its ending year (2024)."""
    start_year, end_year = season.split("-")
    return int(end_year) + 2000 if len(end_year) == 2 else 2000

def convert_year_to_season(year):
    """Convert a year (e.g., 2024) to season format ('2023-24')."""
    return f"{year-1}-{str(year)[-2:]}"

def scrape_total_league_wins_and_teams(season):
    """Scrape or load from CSV the total league wins and teams for a given season."""

    global league_wins_df
    if season != CURRENT_SEASON and league_wins_df is not None and season in league_wins_df["Season"].values:
        row = league_wins_df.loc[league_wins_df["Season"] == season].iloc[0]
        logger.info(f"Loaded from CSV - {season}: Total Wins: {row['Total Wins']}, Total Teams: {row['Total Teams']}")
        return int(row["Total Wins"]), int(row["Total Teams"])

    # scrape data if not found in CSV
    year = convert_season_to_year(season)
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    total_wins, total_teams = 0, 0
    for table_id in ["confs_standings_E", "confs_standings_W"]:
        table = soup.find("table", {"id": table_id})
        if not table:
            raise ValueError(f"Table with id '{table_id}' not found on the page.")

        df = pd.read_html(StringIO(str(table)))[0]
        if "W" not in df.columns:
            raise ValueError(f"Column 'W' not found in the table '{table_id}'. Check table structure.")

        df["W"] = pd.to_numeric(df["W"], errors="coerce")
        total_wins += df["W"].sum()
        total_teams += len(df)

    logger.info(f"Scraped Data - {season}: Total Wins: {int(total_wins)}, Total Teams: {total_teams}")
    return int(total_wins), total_teams

def get_salary_cap(season):
    """Get the salary cap for a given season from a preloaded DataFrame."""

    global salary_cap_df
    if salary_cap_df is None:
        raise ValueError("Salary cap data is missing.")

    row = salary_cap_df[salary_cap_df['Season'] == season]
    if row.empty:
        raise ValueError(f"Season {season} not found in the dataset.")

    salary_cap = row.iloc[0]['Salary Cap']
    logger.info(f"{season} Salary Cap: {salary_cap}")
    return salary_cap

if __name__ == '__main__':
    for year in range(2017, 2019):
        season = convert_year_to_season(year)
        total_wins, total_teams = scrape_total_league_wins_and_teams(season)
        salary_cap = get_salary_cap(season)
