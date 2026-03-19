import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Commercial Development Dashboard", layout="wide")


@st.cache_data
def generate_demo_data(seed: int = 42):
    rng = np.random.default_rng(seed)

    n_customers = 500
    customer_ids = np.arange(1000, 1000 + n_customers)
    segments = rng.choice(["SMB", "Mid-Market", "Enterprise"], size=n_customers, p=[0.55, 0.30, 0.15])
    regions = rng.choice(["Helsinki", "Tampere", "Turku", "Oulu"], size=n_customers, p=[0.45, 0.20, 0.20, 0.15])

    customers = pd.DataFrame({
        "customer_id": customer_ids,
        "segment": segments,
        "region": regions,
    })

    n_orders = 3500
    order_customer_ids = rng.choice(customer_ids, size=n_orders, replace=True)
    order_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 730, size=n_orders), unit="D"
    )

    discount_pct = np.clip(rng.normal(0.08, 0.06, size=n_orders), 0, 0.30)
    quantity = rng.integers(1, 8, size=n_orders)
    unit_price = 1000 + rng.normal(0, 200, size=n_orders)
    net_price = unit_price * (1 - discount_pct)
    revenue = net_price * quantity
    cost = revenue * rng.uniform(0.45, 0.72, size=n_orders)

    orders = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1),
        "customer_id": order_customer_ids,
        "order_date": order_dates,
        "discount_pct": discount_pct.round(4),
        "net_revenue": revenue.round(2),
        "cost": cost.round(2),
    })

    # --- PIPELINE ---
    n_opps = 1200
    opp_customer_ids = rng.choice(customer_ids, size=n_opps, replace=True)
    stages = rng.choice(["Won", "Lost", "Open"], size=n_opps, p=[0.38, 0.37, 0.25])
    cycle_days = rng.integers(10, 140, size=n_opps)

    pipeline = pd.DataFrame({
        "opportunity_id": np.arange(1, n_opps + 1),
        "customer_id": opp_customer_ids,
        "stage": stages,
        "sales_cycle_days": cycle_days,
    })

    return customers, orders, pipeline


st.title("Commercial Development Dashboard")

customers, orders, pipeline = generate_demo_data()

orders_enriched = orders.merge(customers, on="customer_id", how="left")
pipeline_enriched = pipeline.merge(customers, on="customer_id", how="left")

# --- FILTERS ---
with st.sidebar:
    st.header("Filters")

    selected_segments = st.multiselect(
        "Segment",
        options=sorted(orders_enriched["segment"].dropna().unique()),
        default=sorted(orders_enriched["segment"].dropna().unique())
    )

    selected_regions = st.multiselect(
        "Region",
        options=sorted(orders_enriched["region"].dropna().unique()),
        default=sorted(orders_enriched["region"].dropna().unique())
    )

filtered_orders = orders_enriched[
    orders_enriched["segment"].isin(selected_segments)
    & orders_enriched["region"].isin(selected_regions)
].copy()

filtered_pipeline = pipeline_enriched[
    pipeline_enriched["segment"].isin(selected_segments)
    & pipeline_enriched["region"].isin(selected_regions)
].copy()

# --- KPI ---
closed = filtered_pipeline[filtered_pipeline["stage"].isin(["Won", "Lost"])]
won = closed[closed["stage"] == "Won"]

total_revenue = filtered_orders["net_revenue"].sum()
avg_discount = filtered_orders["discount_pct"].mean() * 100 if not filtered_orders.empty else 0
avg_order_value = filtered_orders["net_revenue"].mean() if not filtered_orders.empty else 0
win_rate = (len(won) / len(closed) * 100) if len(closed) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"{total_revenue:,.0f}")
c2.metric("Avg discount %", f"{avg_discount:.1f}%")
c3.metric("Avg order value", f"{avg_order_value:,.0f}")
c4.metric("Win rate %", f"{win_rate:.1f}%")

# --- SEGMENT ---
segment_summary = filtered_orders.groupby("segment", as_index=False).agg(
    revenue=("net_revenue", "sum"),
    avg_discount_pct=("discount_pct", "mean"),
)
segment_summary["avg_discount_pct"] *= 100

# --- REGION ---
region_summary = filtered_orders.groupby("region", as_index=False).agg(
    revenue=("net_revenue", "sum"),
    avg_discount_pct=("discount_pct", "mean"),
)
region_summary["avg_discount_pct"] *= 100

# --- SALES EFFICIENCY BY REGION ---
closed_region = filtered_pipeline[filtered_pipeline["stage"].isin(["Won", "Lost"])]

sales_region = closed_region.groupby("region", as_index=False).agg(
    opportunities=("opportunity_id", "count"),
    won_deals=("stage", lambda x: (x == "Won").sum()),
    avg_cycle=("sales_cycle_days", "mean"),
)

sales_region["win_rate_pct"] = sales_region["won_deals"] / sales_region["opportunities"] * 100

# --- OPPORTUNITY SCORING ---
opportunity_df = region_summary.merge(sales_region, on="region", how="left")

opportunity_df["opportunity_score"] = (
    opportunity_df["avg_discount_pct"] * 0.3
    + (100 - opportunity_df["win_rate_pct"]) * 0.4
    + opportunity_df["avg_cycle"] * 0.3
)

opportunity_df = opportunity_df.sort_values("opportunity_score", ascending=False)

# --- LAYOUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by segment")
    st.dataframe(segment_summary)
    st.bar_chart(segment_summary.set_index("segment")["revenue"])

with col2:
    st.subheader("Revenue by region")
    st.dataframe(region_summary)
    st.bar_chart(region_summary.set_index("region")["revenue"])

st.subheader("Sales efficiency by region")
st.dataframe(sales_region)

st.subheader("Opportunity scoring")
st.dataframe(opportunity_df)

# --- MANAGEMENT SUMMARY ---
st.subheader("Management summary")

if not opportunity_df.empty:
    top = opportunity_df.iloc[0]
    st.write(f"- Highest opportunity region: {top['region']}")
    st.write(f"- Opportunity score: {top['opportunity_score']:.1f}")
    st.write(f"- Win rate: {top['win_rate_pct']:.1f}%")
    st.write(f"- Avg cycle: {top['avg_cycle']:.1f} days")