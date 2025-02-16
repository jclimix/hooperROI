import pytest
import pandas as pd
import requests
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
import chardet
from scrapePlayerPage import *
import logging
logger = logging.getLogger("test_logger")

@pytest.fixture
def mock_player_data():
    return pd.DataFrame({
        "Player Name": ["LeBron James", "Stephen Curry"],
        "Player ID": ["lebron01", "curry01"]
    })

@patch("pandas.read_csv")
def test_get_player_id(mock_read_csv, mock_player_data):
    mock_read_csv.return_value = mock_player_data
    
    assert get_player_id(2023, "LeBron James") == "lebron01"
    assert get_player_id(2023, "Stephen Curry") == "curry01"
    assert get_player_id(2023, "Unknown Player") == "Player not found"

def test_get_player_headshot():
    soup = BeautifulSoup('<div><img src="https://example.com/headshots/curry01.png"></div>', 'html.parser')
    assert get_player_headshot(soup, "curry01") == "https://example.com/headshots/curry01.png"
    
    soup = BeautifulSoup("<div></div>", "html.parser")
    assert get_player_headshot(soup, "unknown") == "static/images/headshot_fallback.png"

def test_scrape_html_table():
    html = '<div><table id="stats"><tr><th>PTS</th></tr><tr><td>30</td></tr></table></div>'
    soup = BeautifulSoup(html, 'html.parser')
    assert scrape_html_table(soup, "stats") is not None
    
    soup = BeautifulSoup("<div></div>", "html.parser")
    assert scrape_html_table(soup, "unknown") is None

def test_html_table_to_df_stats():
    html = '<table><thead><tr><th>PTS</th></tr></thead><tbody><tr><td>30</td></tr></tbody></table>'
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    df = html_table_to_df_stats(table)
    
    assert df is not None
    assert df.shape == (1, 1)
    assert df.columns[0] == "PTS"
    assert df.iloc[0, 0] == "30"

def test_convert_nba_season_to_year():
    assert convert_nba_season_to_year("2019-20") == 2020
    assert convert_nba_season_to_year("2020-21") == 2021
    assert convert_nba_season_to_year("invalid") is None

def test_rearrange_base_stats_df():
    df = pd.DataFrame({"Season": ["2020-21"], "PTS": [25], "AST": [5], "TRB": [8]})
    df_rearranged = rearrange_base_stats_df(df)
    assert "PTS" in df_rearranged.columns
    assert "AST" in df_rearranged.columns

def test_rearrange_adv_stats_df():
    df = pd.DataFrame({"Season": ["2020-21"], "PER": [20], "WS": [5], "TS%": [0.6]})
    df_rearranged = rearrange_adv_stats_df(df)
    assert "PER" in df_rearranged.columns
    assert "WS" in df_rearranged.columns

def test_clean_duplicate_columns():
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4], "A": [5, 6]})
    df_cleaned = clean_duplicate_columns(df)
    assert df_cleaned.shape[1] == 2
