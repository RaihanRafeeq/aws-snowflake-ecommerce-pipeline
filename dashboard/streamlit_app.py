
import streamlit as st
from snowflake.snowpark.context import get_active_session

# Page configuration
st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

# Connect to the active Snowflake session
session = get_active_session()

# Dashboard heading
st.title("🛒 E-commerce Analytics Dashboard")
st.caption("AWS S3 • AWS Lambda • Snowflake")

st.divider()

# Fetch revenue KPIs
query = """
SELECT
    TOTAL_ORDERS,
    GROSS_REVENUE,
    AVG_ORDER_VALUE,
    TOTAL_ITEMS_SOLD
FROM ECOMMERCE_DB.ANALYTICS.VW_REVENUE_KPIS
"""

try:
    df = session.sql(query).to_pandas()

    if df.empty:
        st.warning("No KPI data available.")
    else:
        kpi = df.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Gross Revenue",
                f"{kpi['GROSS_REVENUE']:,.2f}"
            )

        with col2:
            st.metric(
                "Total Orders",
                f"{int(kpi['TOTAL_ORDERS']):,}"
            )

        with col3:
            st.metric(
                "Average Order Value",
                f"{kpi['AVG_ORDER_VALUE']:,.2f}"
            )

        with col4:
            st.metric(
                "Total Items Sold",
                f"{int(kpi['TOTAL_ITEMS_SOLD']):,}"
            )

        st.divider()

        st.success("Dashboard connected to Snowflake successfully!")

except Exception as e:
    st.error(f"Unable to load dashboard data: {e}")

# Monthly revenue trend
st.subheader("📈 Monthly Revenue Trend")

monthly_query = """
SELECT
    SALES_MONTH,
    GROSS_REVENUE,
    TOTAL_ORDERS
FROM ECOMMERCE_DB.ANALYTICS.VW_MONTHLY_SALES
ORDER BY SALES_MONTH
"""

try:
    monthly_df = session.sql(monthly_query).to_pandas()

    if not monthly_df.empty:
        monthly_df["SALES_MONTH"] = (
            monthly_df["SALES_MONTH"].astype(str)
        )

        st.line_chart(
            monthly_df,
            x="SALES_MONTH",
            y="GROSS_REVENUE",
            use_container_width=True
        )

        with st.expander("View Monthly Sales Data"):
            st.dataframe(
                monthly_df,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No monthly sales data available.")

except Exception as e:
    st.error(f"Unable to load monthly sales: {e}")


# Product and category performance
st.divider()
st.subheader("📦 Product & Category Performance")

product_query = """
SELECT
    PRODUCT_NAME,
    GROSS_REVENUE
FROM ECOMMERCE_DB.ANALYTICS.VW_PRODUCT_PERFORMANCE
ORDER BY GROSS_REVENUE DESC
LIMIT 10
"""

category_query = """
SELECT
    CATEGORY,
    GROSS_REVENUE,
    REVENUE_SHARE_PERCENT
FROM ECOMMERCE_DB.ANALYTICS.VW_CATEGORY_PERFORMANCE
ORDER BY GROSS_REVENUE DESC
"""

try:
    product_df = session.sql(product_query).to_pandas()
    category_df = session.sql(category_query).to_pandas()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 10 Products by Revenue**")

        if not product_df.empty:
            st.bar_chart(
                product_df,
                x="PRODUCT_NAME",
                y="GROSS_REVENUE",
                horizontal=True,
                use_container_width=True
            )
        else:
            st.info("No product data available.")

    with col2:
        st.markdown("**Revenue by Category**")

        if not category_df.empty:
            st.bar_chart(
                category_df,
                x="CATEGORY",
                y="GROSS_REVENUE",
                use_container_width=True
            )
        else:
            st.info("No category data available.")

    with st.expander("View Category Revenue Details"):
        st.dataframe(
            category_df,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Unable to load product analytics: {e}")



# ========================================
# CUSTOMER ANALYTICS
# ========================================

st.divider()
st.subheader("👥 Customer Analytics")

customer_kpi_query = """
SELECT
    TOTAL_CUSTOMERS,
    PURCHASING_CUSTOMERS,
    REPEAT_CUSTOMERS,
    REPEAT_PURCHASE_RATE_PERCENT
FROM ECOMMERCE_DB.ANALYTICS.VW_CUSTOMER_KPIS
"""

top_customers_query = """
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    TOTAL_ORDERS,
    TOTAL_SPENT
FROM ECOMMERCE_DB.ANALYTICS.VW_CUSTOMER_PERFORMANCE
ORDER BY TOTAL_SPENT DESC
LIMIT 10
"""

try:
    customer_kpis = session.sql(
        customer_kpi_query
    ).to_pandas()

    top_customers = session.sql(
        top_customers_query
    ).to_pandas()

    if not customer_kpis.empty:
        customer = customer_kpis.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Customers",
            f"{int(customer['TOTAL_CUSTOMERS']):,}"
        )

        c2.metric(
            "Purchasing Customers",
            f"{int(customer['PURCHASING_CUSTOMERS']):,}"
        )

        c3.metric(
            "Repeat Customers",
            f"{int(customer['REPEAT_CUSTOMERS']):,}"
        )

        repeat_rate = customer[
            "REPEAT_PURCHASE_RATE_PERCENT"
        ]

        c4.metric(
            "Repeat Purchase Rate",
            f"{float(repeat_rate):.2f}%"
            if repeat_rate is not None
            else "N/A"
        )

    st.markdown("#### Top 10 Customers by Spending")

    if not top_customers.empty:
        # Use IDs to distinguish customers with identical names.
        top_customers["CUSTOMER_LABEL"] = (
            top_customers["CUSTOMER_NAME"].astype(str)
            + " (#"
            + top_customers["CUSTOMER_ID"].astype(str)
            + ")"
        )

        st.bar_chart(
            top_customers,
            x="CUSTOMER_LABEL",
            y="TOTAL_SPENT",
            horizontal=True,
            use_container_width=True
        )

        with st.expander("View Top Customer Data"):
            st.dataframe(
                top_customers[
                    [
                        "CUSTOMER_ID",
                        "CUSTOMER_NAME",
                        "TOTAL_ORDERS",
                        "TOTAL_SPENT"
                    ]
                ],
                hide_index=True,
                use_container_width=True
            )

except Exception as e:
    st.error(f"Unable to load customer analytics: {e}")



# ========================================
# PAYMENT PERFORMANCE
# ========================================

st.divider()
st.subheader("💳 Payment Performance")

payment_kpi_query = """
SELECT
    TOTAL_PAYMENTS,
    SUCCESSFUL_PAYMENTS,
    PAYMENT_SUCCESS_RATE_PERCENT,
    SUCCESSFUL_PAYMENT_AMOUNT
FROM ECOMMERCE_DB.ANALYTICS.VW_PAYMENT_KPIS
"""

payment_methods_query = """
SELECT
    PAYMENT_METHOD,
    SUM(TOTAL_PAYMENTS) AS PAYMENT_COUNT
FROM ECOMMERCE_DB.ANALYTICS.VW_PAYMENT_PERFORMANCE
GROUP BY PAYMENT_METHOD
ORDER BY PAYMENT_COUNT DESC
"""

reconciliation_query = """
SELECT
    RECONCILIATION_STATUS,
    COUNT(*) AS ORDER_COUNT
FROM ECOMMERCE_DB.ANALYTICS.VW_PAYMENT_RECONCILIATION
GROUP BY RECONCILIATION_STATUS
ORDER BY ORDER_COUNT DESC
"""

try:
    payment_kpis = session.sql(
        payment_kpi_query
    ).to_pandas()

    payment_methods = session.sql(
        payment_methods_query
    ).to_pandas()

    reconciliation = session.sql(
        reconciliation_query
    ).to_pandas()

    if not payment_kpis.empty:
        payment = payment_kpis.iloc[0]

        p1, p2, p3, p4 = st.columns(4)

        p1.metric(
            "Total Payments",
            f"{int(payment['TOTAL_PAYMENTS']):,}"
        )

        p2.metric(
            "Successful Payments",
            f"{int(payment['SUCCESSFUL_PAYMENTS']):,}"
        )

        success_rate = payment[
            "PAYMENT_SUCCESS_RATE_PERCENT"
        ]

        p3.metric(
            "Payment Success Rate",
            f"{float(success_rate):.2f}%"
            if success_rate is not None
            else "N/A"
        )

        p4.metric(
            "Successful Payment Amount",
            f"{payment['SUCCESSFUL_PAYMENT_AMOUNT']:,.2f}"
        )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Payment Methods")

        if not payment_methods.empty:
            st.bar_chart(
                payment_methods,
                x="PAYMENT_METHOD",
                y="PAYMENT_COUNT",
                use_container_width=True
            )

    with col2:
        st.markdown("#### Payment Reconciliation")

        if not reconciliation.empty:
            st.bar_chart(
                reconciliation,
                x="RECONCILIATION_STATUS",
                y="ORDER_COUNT",
                use_container_width=True
            )

    with st.expander("View Payment Reconciliation Details"):
        st.dataframe(
            reconciliation,
            hide_index=True,
            use_container_width=True
        )

except Exception as e:
    st.error(f"Unable to load payment analytics: {e}")


# ========================================
# DASHBOARD FOOTER
# ========================================

st.divider()

st.caption(
    "E-commerce Data Engineering Project | "
    "AWS S3 • AWS Lambda • Snowflake • Streamlit"
)

st.caption(
    "Revenue metrics represent gross order-item value. "
    "They are not necessarily settled payments."
)
