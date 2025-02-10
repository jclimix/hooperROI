from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route("/")
def index():
    # sample df
    df1 = pd.DataFrame({
        "Player": ["LeBron James", "Stephen Curry", "Kevin Durant"],
        "Team": ["LAL", "GSW", "PHX"],
        "Points": [27.2, 25.3, 26.5]
    })

    df2 = pd.DataFrame({
        "Season": ["2022-23", "2023-24", "2024-25"],
        "Champion": ["DEN", "BOS", "MIL"]
    })

    # dataFrames to HTML tables
    table1 = df1.to_html(classes="table table-bordered", index=False)
    table2 = df2.to_html(classes="table table-bordered", index=False)

    # Other variables to pass
    title = "NBA Player Stats & Champions"
    description = "This page displays player statistics and championship winners."

    return render_template("index.html", table1=table1, table2=table2, title=title, description=description)

if __name__ == "__main__":
    app.run(debug=True)
