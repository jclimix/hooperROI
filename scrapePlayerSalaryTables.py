import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd

url = "https://www.basketball-reference.com/players/j/jokicni01.html#all_contract"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

comments = soup.find_all(string=lambda text: isinstance(text, Comment))

contract_table = None

for comment in comments:
    if 'id="contracts_' in comment:
        contract_table = BeautifulSoup(comment, 'html.parser')
        break

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
        print(df)
        
    else:
        print("Contract table was found inside the comment but could not be extracted.")
else:
    print("Contract table not found inside comments.")
