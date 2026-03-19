from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


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
    acquisition_channel = rng.choice(
        ["Outbound", "Inbound", "Partner", "Paid"],
        size=n_customers,
        p=[0.35, 0.35, 0.15, 0.15],
    )
    acquired_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 730, size=n_customers),
        unit="D",
    )

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "segment": segments,
            "region": regions,
            "acquisition_channel": acquisition_channel,
            "acquired_date": acquired_dates,
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
    created_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 700, size=n_opps),
        unit="D",
    )
    stages = rng.choice(["Won", "Lost", "Open"], size=n_opps, p=[0.38, 0.37, 0.25])
    deal_size = np.exp(rng.normal(np.log(12000), 0.75, size=n_opps))
    cycle_days = rng.integers(10, 140, size=n_opps)
    close_dates = created_dates + pd.to_timedelta(cycle_days, unit="D")
    sales_rep = rng.choice(["Aino", "Mika", "Sara", "Joonas", "Emilia"], size=n_opps)

    pipeline = pd.DataFrame(
        {
            "opportunity_id": np.arange(1, n_opps + 1),
            "customer_id": opp_customer_ids,
            "created_date": created_dates,
            "close_date": close_dates,
            "stage": stages,
            "deal_size": deal_size.round(2),
            "sales_cycle_days": cycle_days,
            "sales_rep": sales_rep,
        }
    )

    return customers, orders, pipeline


def load_data():
    customers_path = DATA_DIR / "customers.csv"
    orders_path = DATA_DIR / "orders.csv"
    pipeline_path = DATA_DIR / "sales_pipeline.csv"

    if customers_path.exists() and orders_path.exists() and pipeline_path.exists():
        customers = pd.read_csv(customers_path, parse_dates=["acquired_date"])
        orders = pd.read_csv(orders_path, parse_dates=["order_date"])
        pipeline = pd.read_csv(
            pipeline_path,
            parse_dates=["created_date", "close_date"],
        )
        print("Loaded CSV files from data/")
    else:
        customers, orders, pipeline = generate_demo_data()
        print("CSV files not found. Using generated demo data.")

    return customers, orders, pipeline


def calculate_kpis(orders: pd.DataFrame, pipeline: pd.DataFrame):
    closed = pipeline[pipeline["stage"].isin(["Won", "Lost"])].copy()
    won = closed[closed["stage"] == "Won"].copy()

    revenue = orders["net_revenue"].sum()
    gross_margin_pct = (
        (orders["net_revenue"].sum() - orders["cost"].sum())
        / orders["net_revenue"].sum()
        * 100
    )
    avg_order_value = orders["net_revenue"].mean()
    avg_discount_pct = orders["discount_pct"].mean() * 100
    win_rate_pct = (len(won) / len(closed) * 100) if len(closed) > 0 else 0
    avg_sales_cycle_days = won["sales_cycle_days"].mean() if len(won) > 0 else 0

    print("\n=== KPI SUMMARY ===")
    print(f"Revenue: {revenue:,.2f}")
    print(f"Gross margin %: {gross_margin_pct:.1f}%")
    print(f"Average order value: {avg_order_value:,.2f}")
    print(f"Average discount %: {avg_discount_pct:.1f}%")
    print(f"Win rate %: {win_rate_pct:.1f}%")
    print(f"Average sales cycle (won deals): {avg_sales_cycle_days:.1f} days")


def revenue_by_segment(customers: pd.DataFrame, orders: pd.DataFrame):
    merged = orders.merge(customers, on="customer_id", how="left")

    segment_df = (
        merged.groupby("segment", as_index=False)
        .agg(revenue=("net_revenue", "sum"))
        .sort_values("revenue", ascending=False)
    )

    print("\n=== REVENUE BY SEGMENT ===")
    print(segment_df)

    plt.figure(figsize=(8, 5))
    plt.bar(segment_df["segment"], segment_df["revenue"])
    plt.title("Revenue by Segment")
    plt.xlabel("Segment")
    plt.ylabel("Revenue")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_by_segment.png", dpi=150)
    plt.close()

    segment_df.to_csv(OUTPUT_DIR / "revenue_by_segment.csv", index=False)


def revenue_by_region(customers: pd.DataFrame, orders: pd.DataFrame):
    merged = orders.merge(customers, on="customer_id", how="left")

    region_df = (
        merged.groupby("region", as_index=False)
        .agg(revenue=("net_revenue", "sum"))
        .sort_values("revenue", ascending=False)
    )

    print("\n=== REVENUE BY REGION ===")
    print(region_df)

    plt.figure(figsize=(8, 5))
    plt.bar(region_df["region"], region_df["revenue"])
    plt.title("Revenue by Region")
    plt.xlabel("Region")
    plt.ylabel("Revenue")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "revenue_by_region.png", dpi=150)
    plt.close()

    region_df.to_csv(OUTPUT_DIR / "revenue_by_region.csv", index=False)


def monthly_revenue_trend(orders: pd.DataFrame):
    monthly_df = orders.copy()
    monthly_df["month"] = monthly_df["order_date"].dt.to_period("M").dt.to_timestamp()

    monthly_df = monthly_df.groupby("month", as_index=False).agg(
        revenue=("net_revenue", "sum")
    )

    print("\n=== MONTHLY REVENUE TREND ===")
    print(monthly_df.tail())

    plt.figure(figsize=(10, 5))
    plt.plot(monthly_df["month"], monthly_df["revenue"], marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "monthly_revenue_trend.png", dpi=150)
    plt.close()

    monthly_df.to_csv(OUTPUT_DIR / "monthly_revenue_trend.csv", index=False)


def pricing_analysis(customers: pd.DataFrame, orders: pd.DataFrame):
    merged = orders.merge(customers[["customer_id", "segment"]], on="customer_id", how="left")

    pricing_df = (
        merged.groupby("segment", as_index=False)
        .agg(
            avg_discount_pct=("discount_pct", "mean"),
            avg_order_value=("net_revenue", "mean"),
            total_revenue=("net_revenue", "sum"),
            orders=("order_id", "count"),
        )
        .sort_values("avg_discount_pct", ascending=False)
    )

    pricing_df["avg_discount_pct"] = pricing_df["avg_discount_pct"] * 100

    print("\n=== PRICING ANALYSIS BY SEGMENT ===")
    print(pricing_df)

    plt.figure(figsize=(8, 5))
    plt.bar(pricing_df["segment"], pricing_df["avg_discount_pct"])
    plt.title("Average Discount by Segment")
    plt.xlabel("Segment")
    plt.ylabel("Average Discount %")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "average_discount_by_segment.png", dpi=150)
    plt.close()

    pricing_df.to_csv(OUTPUT_DIR / "pricing_analysis_by_segment.csv", index=False)


def sales_efficiency_analysis(pipeline: pd.DataFrame):
    closed = pipeline[pipeline["stage"].isin(["Won", "Lost"])].copy()

    rep_df = closed.groupby("sales_rep", as_index=False).agg(
        opportunities=("opportunity_id", "count"),
        won_deals=("stage", lambda x: (x == "Won").sum()),
        avg_deal_size=("deal_size", "mean"),
        avg_sales_cycle_days=("sales_cycle_days", "mean"),
    )

    rep_df["win_rate_pct"] = rep_df["won_deals"] / rep_df["opportunities"] * 100
    rep_df = rep_df.sort_values("win_rate_pct", ascending=False)

    print("\n=== SALES EFFICIENCY BY REP ===")
    print(rep_df)

    plt.figure(figsize=(8, 5))
    plt.bar(rep_df["sales_rep"], rep_df["win_rate_pct"])
    plt.title("Win Rate by Sales Rep")
    plt.xlabel("Sales Rep")
    plt.ylabel("Win Rate %")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "win_rate_by_sales_rep.png", dpi=150)
    plt.close()

    rep_df.to_csv(OUTPUT_DIR / "sales_efficiency_by_rep.csv", index=False)


def region_sales_efficiency(customers: pd.DataFrame, pipeline: pd.DataFrame):
    merged = pipeline.merge(customers[["customer_id", "region"]], on="customer_id", how="left")
    closed = merged[merged["stage"].isin(["Won", "Lost"])].copy()

    region_df = closed.groupby("region", as_index=False).agg(
        opportunities=("opportunity_id", "count"),
        won_deals=("stage", lambda x: (x == "Won").sum()),
        avg_sales_cycle_days=("sales_cycle_days", "mean"),
        avg_deal_size=("deal_size", "mean"),
    )

    region_df["win_rate_pct"] = region_df["won_deals"] / region_df["opportunities"] * 100
    region_df = region_df.sort_values("win_rate_pct", ascending=False)

    print("\n=== SALES EFFICIENCY BY REGION ===")
    print(region_df)

    region_df.to_csv(OUTPUT_DIR / "sales_efficiency_by_region.csv", index=False)


def opportunity_scoring(customers: pd.DataFrame, orders: pd.DataFrame, pipeline: pd.DataFrame):
    orders_merged = orders.merge(customers[["customer_id", "region"]], on="customer_id", how="left")
    pipeline_merged = pipeline.merge(customers[["customer_id", "region"]], on="customer_id", how="left")

    region_orders = orders_merged.groupby("region", as_index=False).agg(
        revenue=("net_revenue", "sum"),
        avg_discount_pct=("discount_pct", "mean"),
    )
    region_orders["avg_discount_pct"] = region_orders["avg_discount_pct"] * 100

    closed = pipeline_merged[pipeline_merged["stage"].isin(["Won", "Lost"])].copy()
    region_pipeline = closed.groupby("region", as_index=False).agg(
        opportunities=("opportunity_id", "count"),
        won_deals=("stage", lambda x: (x == "Won").sum()),
        avg_sales_cycle_days=("sales_cycle_days", "mean"),
    )
    region_pipeline["win_rate_pct"] = region_pipeline["won_deals"] / region_pipeline["opportunities"] * 100

    opportunity_df = region_orders.merge(region_pipeline, on="region", how="left")
    opportunity_df["opportunity_score"] = (
        opportunity_df["avg_discount_pct"] * 0.30
        + (100 - opportunity_df["win_rate_pct"]) * 0.40
        + opportunity_df["avg_sales_cycle_days"] * 0.30
    )

    opportunity_df = opportunity_df.sort_values("opportunity_score", ascending=False)

    print("\n=== OPPORTUNITY SCORING BY REGION ===")
    print(opportunity_df)

    opportunity_df.to_csv(OUTPUT_DIR / "opportunity_scoring_by_region.csv", index=False)


def main():
    customers, orders, pipeline = load_data()

    calculate_kpis(orders, pipeline)
    revenue_by_segment(customers, orders)
    revenue_by_region(customers, orders)
    monthly_revenue_trend(orders)
    pricing_analysis(customers, orders)
    sales_efficiency_analysis(pipeline)
    region_sales_efficiency(customers, pipeline)
    opportunity_scoring(customers, orders, pipeline)

    print("\nSaved outputs to ./output")


if __name__ == "__main__":
    main()