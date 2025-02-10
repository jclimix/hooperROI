# HooperROI | Documentation  
**By JME | Universe-J**  

## Overview  
HooperROI is a project designed to assess the value (or return on investment) of NBA player contracts by analyzing player salary data and performance metrics. The key metric, known as the **Overpay Index**, contextualizes a player's salary by comparing it to the league-wide cost per win share and their team's expenditure per win share for said player. This metric determines whether a player is overpaid or underpaid, and the final result is presented as a **Contract Value Rating (CVR)** on a **5⭐ scale**.  

The application is built using Python with libraries such as **Pandas, BeautifulSoup, NumPy,** and **Flask**. The data is sourced from **Basketball Reference**, where salary and performance statistics are scraped and processed to compute a variety of useful metrics including the **Overpay Index** & **Contract Value Rating**. Users can input a given **season** and a **player's name** via a simple web interface and retrieve an analysis of their contract value.  

### **Access the Website:**  
To view the project site, visit [https://hooperROI.universe-j.com](https://hooperROI.universe-j.com).  

---

## **Glossary of Metrics**  
HooperROI evaluates NBA contracts using the following metrics:  

### **1. Salary**  
- The total amount a player is paid for a given season.  
- This data is sourced from **Basketball Reference** and includes guaranteed contract amounts.  

### **2. Win Shares (WS)**  
- A statistic that estimates the number of wins a player contributes to their team.  
- Calculated based on **offensive and defensive performance metrics**.  
- Higher win shares indicate a more valuable player in terms of on-court impact.  

### **3. Salary Cap**  
- The total amount an NBA team is allowed to spend on player salaries in a given season.  
- The **league-wide salary cap** varies from season to season and affects contract negotiations.  

### **4. Average Value Per Win Share (Avg. Value Per WS)**  
- The **league-wide average amount** teams spend per win share in a season.  
- Computed by dividing the **total NBA payroll** by the **total win shares** produced league-wide.  
- This serves as a benchmark for assessing **fair contract value**.  

### **5. Salary Per Win Share**  
- A player's **salary divided by their total win shares** for a season.  
- Indicates how much a team is paying per win share produced by that player.  
- A lower **Salary Per WS** suggests a better **return on investment**.  

### **6. Overpay Index**  
- The ratio between a player's **Salary Per WS** and the **league-wide Average Value Per WS**.  

#### **Interpreting the Overpay Index:**  
- **Overpay Index > 1** → Player is **overpaid** relative to league norms.  
- **Overpay Index < 1** → Player is **underpaid** or a **bargain contract**.  
- **Overpay Index = 1** → Player's salary is exactly at **fair market value**.  

### **7. Salary Adjusted to Value**  
- A **hypothetical salary** a player **should be earning** based on their **win share production** and the **league-wide Avg. Value Per WS**.  
- This metric shows what a **fair market salary** for a player would be if teams paid purely based on **win share production**.  

### **8. Salary Adjusted Percentage**  
- The **percentage difference** between a player’s **actual salary** and their **Salary Adjusted to Value**.  

#### **Interpreting the Salary Adjusted Percentage:**  
- **Positive percentage** → Player is earning **less than their fair value** (potential **bargain**).  
- **Negative percentage** → Player is earning **more than their fair value** (potential **overpay**).  

### **9. Contract Value Rating (CVR)**  
- A **5-star rating system** that simplifies contract evaluations based on the **Overpay Index**.  
- Players with **low Overpay Index values** (indicating **great value contracts**) receive **higher CVRs**.  

#### **General scale:**  
- ★★★★★ (5 stars) → **Elite value** contract (high impact, low salary).  
- ★★★★☆ (4 stars) → **Good value** contract.  
- ★★★☆☆ (3 stars) → **Fairly priced** contract.  
- ★★☆☆☆ (2 stars) → **Slightly overpaid** contract.  
- ★☆☆☆☆ (1 star) → **Highly overpaid** contract.  

---

## **Usage Guide**  

### **Entering Player Data**  
- Users input **season** and an **NBA player's name** into the web application.  
- The web app is only able to scrape/analyze contract data from the **last decade (2016-17 to 2024-25)**.  
- The system fetches the player's **salary and performance statistics** from **Basketball Reference**, calculates different metrics, and outputs the data to a tabular table.  

### **Understanding the Output**  
- **Overpay Index** determines if the player is **overpaid or underpaid**.  
- **CVR provides an easy-to-understand 5-star evaluation**.  
- **Player Per Game and Advanced stats** are provided for additional context.  

### **Data Update Process**  
- **Salary and performance data** are refreshed with each request to ensure **accurate calculations**.  

---

## **Insights**  
The **Overpay Index** and **CVR** are influenced by several factors beyond just raw performance. Below are key insights into how contract value is affected by various player conditions:  

### **1. Impact of Injuries and Load Management**  
- Players who **miss a significant number of games** due to injuries or load management still receive their **full salary**, which inflates their **Overpay Index** since they contribute **fewer win shares** while maintaining the same salary.  
- As a result, their **CVR decreases**, reflecting a lower **return on investment** for the team.  

### **2. Star Players vs. Role Players**  
- **Superstars** may still have a high **Overpay Index** despite strong performance if their contracts are significantly above **league-average spending per win share**.  
- **Role players** on **team-friendly deals** often have **lower Overpay Index values** and a **higher CVR** due to their cost-efficient contributions.  

### **3. Teams with Inefficient Spending**  
- Some teams consistently **overpay for win shares** due to **poor roster construction**, leading to an **inflated Overpay Index** for multiple players on their payroll.  

### **4. Young Players vs. Veteran Players**  
- **Rookie-scale contracts** often produce **extremely favorable Overpay Index values**, as young stars contribute significant **win shares** at a **lower salary**.  
- **Veterans on max contracts** need to **maintain elite performance levels** to justify their salaries; otherwise, they will rank poorly in both **Overpay Index** and **CVR**.  

---

## **Technical Details**  
### **Core Technologies:**  
- **Python**: Core programming language for data processing.  
- **Flask**: Web framework used for the interface.  
- **Pandas & NumPy**: Handles data manipulation and statistical calculations.  
- **BeautifulSoup**: Web scraping tool used to collect salary and stats data.  

### **Data Storage & Processing:**  
- Player **salary and win share data** are extracted from **Basketball Reference**.  
- Data is **cleaned and structured** using **Pandas** before analysis.  
- The **Overpay Index** and **CVR** are computed dynamically based on the **latest data**.  

---

## **Troubleshooting & Support**  
For further assistance, contact **jmge.work@gmail.com**.  

---

## **Summary**  
HooperROI provides an **easy way** to evaluate **NBA player contracts** by integrating **player salary data** with **performance metrics**.  

The **Overpay Index** determines whether a player is **overpaid or underpaid**, and the **Contract Value Rating (CVR)** presents this analysis in an intuitive **5-star format**.  

With **automated data retrieval** and a **simple web interface**, users can quickly assess **contract efficiency and value** for NBA players.  
