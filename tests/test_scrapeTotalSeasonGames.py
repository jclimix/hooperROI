import pytest
import pandas as pd
import requests
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
import os
from io import StringIO
from scrapeTotalSeasonGames import *  

import logging
logger = logging.getLogger("test_logger")

@patch("os.path.exists", return_value=True)
@patch("pandas.read_csv")
def test_load_csv_files(mock_read_csv, mock_exists):
    mock_read_csv.return_value = pd.DataFrame({"Season": ["2023-24"], "Total Wins": [1230], "Total Teams": [30]})
    global league_wins_df
    league_wins_df = pd.read_csv(LEAGUE_WINS_CSV)
    assert league_wins_df is not None
    assert "Season" in league_wins_df.columns

def test_convert_season_to_year():
    assert convert_season_to_year("2023-24") == 2024
    assert convert_season_to_year("2019-20") == 2020
    assert convert_season_to_year("2000-01") == 2001

def test_convert_year_to_season():
    assert convert_year_to_season(2024) == "2023-24"
    assert convert_year_to_season(2000) == "1999-00"

def test_scrape_total_league_wins_and_teams_csv():
    global league_wins_df
    league_wins_df = pd.DataFrame({"Season": ["2023-24"], "Total Wins": [1230], "Total Teams": [30]})
    total_wins, total_teams = scrape_total_league_wins_and_teams("2023-24")
    assert total_wins == 1230
    assert total_teams == 30

@patch("requests.get")
def test_scrape_total_league_wins_and_teams_web(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<html><table id="confs_standings_E"><tr><th>W</th></tr><tr><td>600</td></tr></table><table id="confs_standings_W"><tr><th>W</th></tr><tr><td>630</td></tr></table></html>'
    mock_get.return_value = mock_response
    
    total_wins, total_teams = scrape_total_league_wins_and_teams("2024-25")
    assert total_wins == 1230
    assert total_teams == 2

@patch("pandas.read_csv")
def test_get_salary_cap(mock_read_csv):
    mock_read_csv.return_value = pd.DataFrame({"Season": ["2023-24"], "Salary Cap": ["$136,021,000"]})
    global salary_cap_df
    salary_cap_df = pd.read_csv(SALARY_CAP_CSV)
    
    salary_cap = get_salary_cap("2023-24")
    assert salary_cap == "$136,021,000"

    with pytest.raises(ValueError, match="Season 2025-26 not found in the dataset."):
        get_salary_cap("2025-26")
