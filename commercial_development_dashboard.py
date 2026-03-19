import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Commercial Development Dashboard", layout="wide")


@st.cache_data
def generate_demo_data(seed: int = 42):
    rng = np.random.default_rng(seed)

    # -----------------------------
    # Customers
    # -----------------------------
    n_customers = 500
    customer_ids = np.arange(1000, 1000 + n_customers)

    segments = rng.choice(
        ["SMB", "Mid-Market", "Enterprise"],
        size=n_customers,
        p=[0.55, 0.30, 0.15],
    )
    regions = rng.choice(
        ["Helsinki", "Tampere", "Turku", "Oulu"],
        size=n_customers,
        p=[0.45, 0.20, 0.20, 0.15],
    )

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "segment": segments,
            "region": regions,
        }
    )

    # -----------------------------
    # Orders
    # -----------------------------
    n_orders = 3500
    order_customer_ids = rng.choice(customer_ids, size=n_orders, replace=True)
    order_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 730, size=n_orders),
        unit="D",
    )

    product_family = rng.choice(
        ["Core", "Premium", "Add-on"],
        size=n_orders,
        p=[0.55, 0.25, 0.20],
    )

    base_price = np.select(
        [
            product_family == "Core",
            product_family == "Premium",
            product_family == "Add-on",
        ],
        [800, 1800, 400],
        default=700,
    )

    discount_pct = np.clip(rng.normal(0.08, 0.06, size=n_orders), 0, 0.30)
    quantity = rng.integers(1, 8, size=n_orders)
    unit_price = base_price * (1 + rng.normal(0, 0.08, size=n_orders))
    net_price = unit_price * (1 - discount_pct)
    revenue = net_price * quantity
    cost = revenue * rng.uniform(0.45, 0.72, size=n_orders)

    orders = pd.DataFrame(
        {
            "order_id": np.arange(1, n_orders + 1),
            "customer_id": order_customer_ids,
            "order_date": order_dates,
            "product_family": product_family,
            "quantity": quantity,
            "list_price": unit_price.round(2),
            "discount_pct": discount_pct.round(4),
            "net_revenue": revenue.round(2),
            "cost": cost.round(2),
        }
    )

    # -----------------------------
    # Pipeline
    # -----------------------------
    n_opps = 1200
    opp_customer_ids = rng.choice(customer_ids, size=n_opps, replace=True)
    stages = rng.choice(["Won", "Lost", "Open"], size=n_opps, p=[0.38, 0.37, 0.25])
    cycle_days = rng.integers(10, 140, size=n_opps)
    sales_rep = rng.choice(["Aino", "Mika", "Sara", "Joonas", "Emilia"], size=n_opps)

    pipeline = pd.DataFrame(
        {
            "opportunity_id": np.arange(1, n_opps + 1),
            "customer_id": opp_customer_ids,
            "stage": stages,
            "sales_cycle_days": cycle_days,
            "sales_rep": sales_rep,
        }
    )

    return customers, orders, pipeline


st.title("Commercial Development Dashboard")

customers, orders, pipeline = generate_demo_data()

orders_enriched = orders.merge(customers, on="customer_id", how="left")
pipeline_enriched = pipeline.merge(customers, on="customer_id", how="left")

# -----------------------------
# Filters
# -----------------------------
with st.sidebar:
    st.header("Filters")

    selected_segments = st.multiselect(
        "Segment",
        options=sorted(orders_enriched["segment"].dropna().unique()),
        default=sorted(orders_enriched["segment"].dropna().unique()),
    )

    selected_regions = st.multiselect(
        "Region",
        options=sorted(orders_enriched["region"].dropna().unique()),
        default=sorted(orders_enriched["region"].dropna().unique()),
    )

    selected_products = st.multiselect(
        "Product family",
        options=sorted(orders_enriched["product_family"].dropna().unique()),
        default=sorted(orders_enriched["product_family"].dropna().unique()),
    )

filtered_orders = orders_enriched[
    orders_enriched["segment"].isin(selected_segments)
    & orders_enriched["region"].isin(selected_regions)
    & orders_enriched["product_family"].isin(selected_products)
].copy()

filtered_pipeline = pipeline_enriched[
    pipeline_enriched["segment"].isin(selected_segments)
    & pipeline_enriched["region"].isin(selected_regions)
].copy()

closed = filtered_pipeline[filtered_pipeline["stage"].isin(["Won", "Lost"])].copy()
won = closed[closed["stage"] == "Won"].copy()

# -----------------------------
# KPI cards
# -----------------------------
total_revenue = filtered_orders["net_revenue"].sum()
gross_margin_pct = (
    ((filtered_orders["net_revenue"].sum() - filtered_orders["cost"].sum()) / filtered_orders["net_revenue"].sum()) * 100
    if filtered_orders["net_revenue"].sum() > 0
    else 0
)
avg_discount = filtered_orders["discount_pct"].mean() * 100 if not filtered_orders.empty else 0
avg_order_value = filtered_orders["net_revenue"].mean() if not filtered_orders.empty else 0
win_rate = (len(won) / len(closed) * 100) if len(closed) else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Revenue", f"{total_revenue:,.0f}")
c2.metric("Gross margin %", f"{gross_margin_pct:.1f}%")
c3.metric("Avg discount %", f"{avg_discount:.1f}%")
c4.metric("Avg order value", f"{avg_order_value:,.0f}")
c5.metric("Win rate %", f"{win_rate:.1f}%")

# -----------------------------
# Revenue trend
# -----------------------------
st.subheader("Revenue trend")

monthly_df = filtered_orders.copy()
if not monthly_df.empty:
    monthly_df["month"] = monthly_df["order_date"].dt.to_period("M").dt.to_timestamp()
    monthly_df = monthly_df.groupby("month", as_index=False).agg(
        revenue=("net_revenue", "sum")
    )
    st.line_chart(monthly_df.set_index("month")["revenue"])
else:
    st.info("No data available for the selected filters.")

# -----------------------------
# Segment and Region summaries
# -----------------------------
segment_summary = filtered_orders.groupby("segment", as_index=False).agg(
    revenue=("net_revenue", "sum"),
    avg_discount_pct=("discount_pct", "mean"),
    avg_order_value=("net_revenue", "mean"),
    orders=("order_id", "count"),
)
if not segment_summary.empty:
    segment_summary["avg_discount_pct"] *= 100

region_summary = filtered_orders.groupby("region", as_index=False).agg(
    revenue=("net_revenue", "sum"),
    avg_discount_pct=("discount_pct", "mean"),
    avg_order_value=("net_revenue", "mean"),
    orders=("order_id", "count"),
)
if not region_summary.empty:
    region_summary["avg_discount_pct"] *= 100

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by segment")
    st.dataframe(segment_summary, use_container_width=True)
    if not segment_summary.empty:
        st.bar_chart(segment_summary.set_index("segment")["revenue"])

with col2:
    st.subheader("Revenue by region")
    st.dataframe(region_summary, use_container_width=True)
    if not region_summary.empty:
        st.bar_chart(region_summary.set_index("region")["revenue"])

# -----------------------------
# Pricing analysis
# -----------------------------
st.subheader("Pricing analysis")

pricing_df = filtered_orders.groupby(["product_family", "segment"], as_index=False).agg(
    avg_list_price=("list_price", "mean"),
    avg_discount_pct=("discount_pct", "mean"),
    avg_net_revenue=("net_revenue", "mean"),
    orders=("order_id", "count"),
)
if not pricing_df.empty:
    pricing_df["avg_discount_pct"] *= 100

st.dataframe(pricing_df, use_container_width=True)

# -----------------------------
# Sales efficiency by region
# -----------------------------
st.subheader("Sales efficiency by region")

sales_region = closed.groupby("region", as_index=False).agg(
    opportunities=("opportunity_id", "count"),
    won_deals=("stage", lambda x: (x == "Won").sum()),
    avg_cycle=("sales_cycle_days", "mean"),
)
if not sales_region.empty:
    sales_region["win_rate_pct"] = sales_region["won_deals"] / sales_region["opportunities"] * 100
    sales_region = sales_region.sort_values("win_rate_pct", ascending=False)

st.dataframe(sales_region, use_container_width=True)

# -----------------------------
# Sales efficiency by rep
# -----------------------------
st.subheader("Sales efficiency by rep")

rep_df = closed.groupby("sales_rep", as_index=False).agg(
    opportunities=("opportunity_id", "count"),
    won_deals=("stage", lambda x: (x == "Won").sum()),
    avg_cycle=("sales_cycle_days", "mean"),
)
if not rep_df.empty:
    rep_df["win_rate_pct"] = rep_df["won_deals"] / rep_df["opportunities"] * 100
    rep_df = rep_df.sort_values("win_rate_pct", ascending=False)

st.dataframe(rep_df, use_container_width=True)

if not rep_df.empty:
    st.bar_chart(rep_df.set_index("sales_rep")["win_rate_pct"])

# -----------------------------
# Opportunity scoring
# -----------------------------
st.subheader("Opportunity scoring")

opportunity_df = region_summary.merge(sales_region, on="region", how="left") if not region_summary.empty else pd.DataFrame()

if not opportunity_df.empty:
    opportunity_df["opportunity_score"] = (
        opportunity_df["avg_discount_pct"] * 0.30
        + (100 - opportunity_df["win_rate_pct"]) * 0.40
        + opportunity_df["avg_cycle"] * 0.30
    )
    opportunity_df = opportunity_df.sort_values("opportunity_score", ascending=False)

st.dataframe(opportunity_df, use_container_width=True)

# -----------------------------
# Management summary
# -----------------------------
st.subheader("Management summary")

summary_lines = []

if not segment_summary.empty:
    top_segment = segment_summary.sort_values("revenue", ascending=False).iloc[0]
    summary_lines.append(
        f"Top revenue segment: {top_segment['segment']} ({top_segment['revenue']:,.0f} revenue)."
    )

if not region_summary.empty:
    top_region = region_summary.sort_values("revenue", ascending=False).iloc[0]
    summary_lines.append(
        f"Top revenue region: {top_region['region']} ({top_region['revenue']:,.0f} revenue)."
    )

if not rep_df.empty:
    top_rep = rep_df.sort_values("win_rate_pct", ascending=False).iloc[0]
    summary_lines.append(
        f"Best sales rep by win rate: {top_rep['sales_rep']} ({top_rep['win_rate_pct']:.1f}% win rate)."
    )

if not opportunity_df.empty:
    top_opp = opportunity_df.iloc[0]
    summary_lines.append(
        f"Highest-priority opportunity region: {top_opp['region']} (score {top_opp['opportunity_score']:.1f})."
    )

if summary_lines:
    for line in summary_lines:
        st.write(f"- {line}")
else:
    st.write("No summary available for the selected filters.")