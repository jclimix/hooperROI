import pytest
import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
from unittest.mock import patch, MagicMock
import chardet
from scrapeSalaryData import *
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

@patch("requests.get")
def test_scrape_html(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<html><head></head><body></body></html>"
    mock_get.return_value = mock_response
    mock_detect = {"encoding": "utf-8"}
    with patch("chardet.detect", return_value=mock_detect):
        soup = scrape_html("curry01")
        assert isinstance(soup, BeautifulSoup)

    mock_response.status_code = 404
    soup = scrape_html("invalid_player")
    assert soup is None

def test_scrape_html_table():
    html = '<div><table id="stats"><tr><th>PTS</th></tr><tr><td>30</td></tr></table></div>'
    soup = BeautifulSoup(html, 'html.parser')
    assert scrape_html_table(soup, "stats") is not None
    
    soup = BeautifulSoup("<div></div>", "html.parser")
    assert scrape_html_table(soup, "unknown") is None

def test_scrape_html_current_salary_table():
    html = '<!--<table id="contracts_"><tr><th>Year</th></tr></table>-->'
    soup = BeautifulSoup(html, "html.parser")
    assert scrape_html_current_salary_table(soup) is not None

def test_html_table_to_df_adv():
    html = '<table><thead><tr><th>PTS</th></tr></thead><tbody><tr><td>30</td></tr></tbody></table>'
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    df = html_table_to_df_adv(table)
    
    assert df is not None
    assert df.shape == (1, 1)
    assert df.columns[0] == "PTS"
    assert df.iloc[0, 0] == "30"

def test_html_table_to_df_past_salary():
    html = '<table><thead><tr><th>Year</th></tr></thead><tbody><tr><td>2022</td></tr></tbody></table>'
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    df = html_table_to_df_past_salary(table)
    
    assert df is not None
    assert df.shape == (1, 1)
    assert df.columns[0] == "Year"
    assert df.iloc[0, 0] == "2022"

def test_html_table_to_df_current_salary():
    html = '<table><tr class="thead"><th>Year</th></tr><tr><td>2024</td></tr></table>'
    soup = BeautifulSoup(html, "html.parser")
    df = html_table_to_df_current_salary(soup)
    
    assert df is not None
    assert df.shape == (1, 1)
    assert df.columns[0] == "Year"
    assert df.iloc[0, 0] == "2024"

def test_convert_nba_season_to_year():
    assert convert_nba_season_to_year("2019-20") == 2020
    assert convert_nba_season_to_year("2020-21") == 2021
    assert convert_nba_season_to_year("invalid") is None

def test_money_to_float():
    assert money_to_float("$1,000,000") == 1000000.0
    assert money_to_float("$50,000") == 50000.0
    assert money_to_float("invalid") == 0.0
