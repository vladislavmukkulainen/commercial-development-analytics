# commercial-development-analytics
Python project analyzing growth, pricing, and sales efficiency opportunities.

# Commercial Development Analytics

## Overview
This project demonstrates how commercial analytics can be used to identify opportunities in growth, pricing, and sales efficiency.

The analysis combines transaction data and sales pipeline data to uncover where a company can improve revenue quality, optimize pricing, and increase sales performance.

---

## Business Problem
Many companies grow revenue without understanding:
- Which customer segments actually drive value
- Where pricing discipline is weak
- How efficient the sales organization is
- Where the biggest commercial improvement opportunities are

This project answers:
> Where should a company focus to improve commercial performance?

---

## Analytical Approach
The analysis is structured into four main areas:

### 1. Revenue Analysis
- Revenue by segment
- Revenue by region
- Monthly revenue trend

### 2. Pricing Analysis
- Average discount by segment
- Average order value
- Revenue vs discount relationship

### 3. Sales Efficiency
- Win rate
- Sales cycle length
- Sales performance by rep
- Sales efficiency by region

### 4. Opportunity Scoring
- Combines:
  - Discount levels
  - Win rate
  - Sales cycle length
- Identifies highest-priority regions for improvement

---

## Key Findings (Example from demo data)
- SMB is the largest revenue driver
- Enterprise customers have the highest discounts and highest order values
- Sales performance varies significantly between regions
- Some regions show lower win rates and longer sales cycles → clear improvement potential

---

## Business Recommendations
- Improve pricing discipline in high-discount segments
- Focus sales enablement on low win-rate regions
- Reduce sales cycle length in underperforming areas
- Prioritize regions with highest opportunity score

---

## Project Structure

commercial-development-analytics/
│
├── commercial_development_analytics_project.py
├── commercial_development_dashboard.py
├── output/
└── README.md


---

## How to Run

### 1. Install dependencies

pip install pandas numpy matplotlib streamlit

### 2. Run analysis

python commercial_development_analytics_project.py


### 3. Run dashboard

streamlit run commercial_development_dashboard.py


---

## Dashboard
The project includes an interactive Streamlit dashboard with:
- KPI overview (revenue, discount, win rate)
- Segment and region analysis
- Sales efficiency metrics
- Opportunity scoring
- Management summary

---

## About
This project was built as part of a data analytics portfolio to demonstrate:
- Business-oriented data analysis
- Commercial thinking (growth, pricing, sales)
- Python-based analytics and visualization
- End-to-end problem solving
