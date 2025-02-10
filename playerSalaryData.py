from scrapeSalaryData import *
from scrapeTotalSeasonGames import *
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)

def format_to_dollars(amount: float) -> str:
    return f"${amount:,.2f}"

def pct_diff(old: float, new: float) -> str:
    """Calculates the percentage difference between two values."""
    if old == 0:
        return "0"  # Return 0 if the old value is 0 to avoid division by zero
    try:
        diff: float = ((new - old) / abs(old)) * 100
        sign: str = "+" if diff >= 0 else "-"
        return f"{sign}{abs(diff):.2f}"
    except Exception as e:
        logger.error(f"Error calculating percentage difference: {e}")
        return "0"

def calc_nba_payroll(total_teams: int, salary_cap: float) -> float:
    """Calculates the total NBA payroll."""
    return float(total_teams) * float(salary_cap)

def calc_value_of_win_share(nba_payroll: float, total_wins: int) -> float:
    """Calculates the monetary value of one win share."""
    return nba_payroll / float(total_wins)

def calc_salary_per_win_share(salary: float, win_shares: float) -> float:
    """Calculates how much a player earns per win share."""
    if win_shares != 0.0:
        return float(salary) / float(win_shares)
    else:
        return 0.0

def calc_overpay_index(salary_per_ws: float, value_of_ws: float) -> float:
    """Calculates the overpay index based on salary per WS vs league average."""
    return round((salary_per_ws / value_of_ws), 2)

def calc_adjusted_salary(salary: float, overpay_index: float) -> float:
    """Calculates the adjusted salary based on value per WS."""
    if overpay_index != 0:
        return (1 / overpay_index) * salary
    else:
        return 0.0

def calc_contract_value_rating(overpay_index, max_overpay_index=10.0):

    if overpay_index != 0:

        max_overpay_index = max(max_overpay_index, 1.1)

        # normalize overpay index to 0.0 - 5.0 scale
        if overpay_index <= 1.0:
            contract_value_rating = 5.0  # "perfect" contract
        else:
            contract_value_rating = max(0.0, 5.0 * (1 - ((overpay_index - 1) / (max_overpay_index - 1))))

        return round(contract_value_rating, 2)
    
    else:
        return 0.0

def get_recent_seasons(df):

    if "Season" not in df.columns:
        raise ValueError("The DataFrame does not contain a 'Season' column.")
    
    return df[df["Season"] >= "2016-17"]["Season"].astype(str).tolist()

def scrape_player_data(player_name, season):

    # func reduces requests to avoid rate limits

    year = convert_season_to_year(season)

    player_id = get_player_id(year, player_name)
    soup_data = scrape_html(player_id)

    return soup_data

def create_player_salary_analysis_df(soup_data, season):
    
    # scrape and process advanced stats table
    adv_table = scrape_html_table(soup_data, table_id="advanced")
    adv_table_df = html_table_to_df_adv(adv_table)
    win_shares = adv_table_df.loc[adv_table_df["Season"] == season, "WS"].values[0]

    print(adv_table_df)

    seasons_list = get_recent_seasons(adv_table_df)
    print(seasons_list)

    all_seasons_data = []

    for season in seasons_list:

        win_shares = adv_table_df.loc[adv_table_df["Season"] == season, "WS"].values[0]
        print(f"Win Shares {season}: {win_shares}")

        if isinstance(win_shares, np.ndarray):
            # convert non-empty values to float
            win_shares = [float(ws) for ws in win_shares if str(ws).strip() != ""]

            if len(win_shares) == 0:
                print(f"No valid win shares found for season {season}. Setting value to 0.0.")
                win_shares = 0.0  # default to 0
            else:
                win_shares = win_shares[0]  # extract the first valid value

        elif isinstance(win_shares, (int, float)):
            pass  # already a valid number

        elif isinstance(win_shares, str):
            if len(win_shares) == 0:
                print(f"No valid win shares found for season {season}. Setting value to 0.0.")
                win_shares = 0.0  # set default value
            else:
                win_shares = float(win_shares.strip())  # convert single string to float

        else:
            raise TypeError(f"Unexpected type for win shares: {type(win_shares)}, Value: {win_shares}")

        # scrape and process salary data
        salary_table = scrape_html_table(soup_data, table_id="all_salaries")
        salary_table_df = html_table_to_df_past_salary(salary_table)

        if salary_table_df is not None and season in salary_table_df["Season"].values:
            salary = salary_table_df.loc[salary_table_df["Season"] == season, "Salary"].values[0]
        else:
            salary_table = scrape_html_current_salary_table(soup_data)
            salary_table_df = html_table_to_df_current_salary(salary_table)
            salary = salary_table_df[season].iloc[0]

        # print(f"Salary: {salary}")
        salary = money_to_float(salary)

        # Scrape league-wide data
        total_wins, total_teams = scrape_total_league_wins_and_teams(season)
        salary_cap = money_to_float(get_salary_cap(season))

        # Perform calculations
        nba_payroll = calc_nba_payroll(total_teams, salary_cap)
        value_of_ws = calc_value_of_win_share(nba_payroll, total_wins)
        salary_per_ws = calc_salary_per_win_share(salary, win_shares)
        overpay_index = calc_overpay_index(salary_per_ws, value_of_ws)
        salary_adjusted = calc_adjusted_salary(salary, overpay_index)
        adjusted_pct = pct_diff(salary, salary_adjusted)
        contract_value_rating = calc_contract_value_rating(overpay_index)

        # print(f"NBA Payroll: {format_to_dollars(nba_payroll)}")
        # print(f"Value of 1 Win Share: {format_to_dollars(value_of_ws)}")
        # print(f"Salary Per Win Share: {format_to_dollars(salary_per_ws)}")
        # print(f"Overpay Index for {player_name}: {round(overpay_index, 2)}")
        # print(f"Salary Adjusted to Value: {format_to_dollars(salary_adjusted)} ({adjusted_pct}%)")
        # print(f"Contract Value Rating for {player_name}: {contract_value_rating}")

        # Create DataFrame (Fix: wrap dictionary in a list)
        all_seasons_data.append({
            "Season": season,
            "Salary": format_to_dollars(salary),
            "Win Shares (WS)": round(win_shares, 1),
            "Salary Cap": format_to_dollars(salary_cap),
            # "NBA Payroll": format_to_dollars(nba_payroll),
            "Avg. Value Per WS": format_to_dollars(value_of_ws),
            "Salary Per WS": format_to_dollars(salary_per_ws),
            "Overpay Index": round(overpay_index, 2),
            "Salary Adjusted to Value": format_to_dollars(salary_adjusted),
            "Salary Adjusted Percentage": (adjusted_pct) + "%",
            "Contract Value Rating": contract_value_rating
        })

    return pd.DataFrame(all_seasons_data)

if __name__ == '__main__':
    player_name = "Ben Simmons"
    season = "2024-25"
    html_soup_data = scrape_player_data(player_name, season)
    analysis_df = create_player_salary_analysis_df(html_soup_data, season)
    print(f"\n")
    print(analysis_df)
