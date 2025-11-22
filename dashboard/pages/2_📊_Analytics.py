import streamlit as st
import asyncio
import pandas as pd
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import get_summary, get_monthly_analytics, get_top_vendors, get_vendors, get_invoices
from utils.chart_builder import ChartBuilder

# Add app directory to path to import formatters
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
from app.utils.formatters import format_currency

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

st.title("📊 Analytics Dashboard")
st.markdown("Visualize spending trends, vendor metrics, and invoice insights.")

# Load data
try:
    summary = asyncio.run(get_summary())
    monthly_data = asyncio.run(get_monthly_analytics())
    top_vendors_data = asyncio.run(get_top_vendors(limit=10))

    # KPI Cards
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Spent",
            value=format_currency(summary['total_spent'])
        )

    with col2:
        st.metric(
            label="Total Invoices",
            value=f"{summary['total_invoices']:,}"
        )

    with col3:
        st.metric(
            label="Total Vendors",
            value=f"{summary['total_vendors']:,}"
        )

    with col4:
        st.metric(
            label="Average Invoice",
            value=format_currency(summary['average_invoice'])
        )

    st.markdown("---")

    # Monthly Trend Chart
    st.markdown("### Monthly Spending Trend")

    if monthly_data['data']:
        df_monthly = pd.DataFrame(monthly_data['data'])
        df_monthly['date'] = pd.to_datetime(
            df_monthly['year'].astype(str) + '-' +
            df_monthly['month'].astype(str) + '-01'
        )
        df_monthly = df_monthly.sort_values('date')

        # Spending line chart
        fig_line = ChartBuilder.create_line_chart(
            data=df_monthly,
            x='date',
            y='total',
            title="Total Spending by Month",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            height=400
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Invoice count bar chart
        fig_count = ChartBuilder.create_simple_bar_chart(
            data=df_monthly,
            x='date',
            y='count',
            title="Invoice Count by Month",
            height=300
        )
        st.plotly_chart(fig_count, use_container_width=True)

    else:
        st.info("No monthly data available yet. Upload invoices to see trends.")

    st.markdown("---")

    # Top Vendors
    st.markdown("### Top Vendors by Spending")

    if top_vendors_data['vendors']:
        col1, col2 = st.columns(2)

        with col1:
            # Bar chart
            df_vendors = pd.DataFrame(top_vendors_data['vendors'])

            fig_vendors = ChartBuilder.create_horizontal_bar_chart(
                data=df_vendors,
                x='total_spent',
                y='normalized_name',
                title='Top 10 Vendors',
                color='total_spent',
                color_continuous_scale='Blues',
                height=500,
                xaxis_title='Total Spent ($)',
                yaxis_title='Vendor'
            )
            st.plotly_chart(fig_vendors, use_container_width=True)

        with col2:
            # Pie chart
            fig_pie = ChartBuilder.create_pie_chart(
                data=df_vendors.head(5),
                values='total_spent',
                names='normalized_name',
                title='Top 5 Vendors - Spending Distribution',
                height=500
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Vendor table
        st.markdown("#### Vendor Details")
        df_vendors['total_spent'] = df_vendors['total_spent'].apply(format_currency)
        st.dataframe(
            df_vendors,
            column_config={
                "normalized_name": "Vendor",
                "total_spent": "Total Spent",
                "invoice_count": "Invoices"
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info("No vendor data available yet. Upload invoices to see vendor analytics.")

    st.markdown("---")

    # Invoice Category Analytics
    st.markdown("### Spending by Category")

    invoices_data = asyncio.run(get_invoices())
    if invoices_data['invoices']:
        df_invoices = pd.DataFrame(invoices_data['invoices'])

        # Category breakdown
        if 'category' in df_invoices.columns and 'total_amount' in df_invoices.columns:
            # Convert total_amount to numeric if it's a string
            if df_invoices['total_amount'].dtype == 'object':
                df_invoices['total_amount'] = pd.to_numeric(df_invoices['total_amount'], errors='coerce')

            category_spending = df_invoices.groupby('category').agg({
                'total_amount': 'sum',
                'id': 'count'
            }).reset_index()
            category_spending.columns = ['category', 'total_spent', 'invoice_count']
            category_spending = category_spending.sort_values('total_spent', ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                # Pie chart of spending by category
                fig_cat_pie = ChartBuilder.create_pie_chart(
                    data=category_spending,
                    values='total_spent',
                    names='category',
                    title='Spending Distribution by Category',
                    color_discrete_sequence=ChartBuilder.COLORS['qualitative']
                )
                st.plotly_chart(fig_cat_pie, use_container_width=True)

            with col2:
                # Bar chart of spending by category
                fig_cat_bar = ChartBuilder.create_colored_bar_chart(
                    data=category_spending,
                    x='category',
                    y='total_spent',
                    title='Total Spending by Category',
                    color_by='total_spent'
                )
                st.plotly_chart(fig_cat_bar, use_container_width=True)

            # Category details table
            st.markdown("#### Category Breakdown")
            category_spending['total_spent'] = category_spending['total_spent'].apply(format_currency)
            st.dataframe(
                category_spending,
                column_config={
                    "category": "Category",
                    "total_spent": "Total Spent",
                    "invoice_count": "Invoice Count"
                },
                hide_index=True,
                use_container_width=True
            )

        st.markdown("---")

        # Recurring vs One-Time Analysis
        st.markdown("### Recurring vs One-Time Purchases")

        if 'is_recurring' in df_invoices.columns:
            recurring_stats = df_invoices.groupby('is_recurring').agg({
                'total_amount': 'sum',
                'id': 'count'
            }).reset_index()
            recurring_stats.columns = ['is_recurring', 'total_spent', 'invoice_count']
            recurring_stats['type'] = recurring_stats['is_recurring'].apply(
                lambda x: 'Recurring' if x else 'One-Time'
            )

            col1, col2 = st.columns(2)

            with col1:
                # Pie chart of recurring vs one-time
                fig_recurring = ChartBuilder.create_pie_chart(
                    data=recurring_stats,
                    values='total_spent',
                    names='type',
                    title='Recurring vs One-Time Spending',
                    color_discrete_map={'Recurring': ChartBuilder.COLORS['accent'], 'One-Time': ChartBuilder.COLORS['primary']}
                )
                st.plotly_chart(fig_recurring, use_container_width=True)

            with col2:
                # Bar comparison
                fig_recurring_bar = ChartBuilder.create_category_bar_chart(
                    data=recurring_stats,
                    x='type',
                    y='invoice_count',
                    title='Recurring vs One-Time Invoice Count',
                    color_by='type'
                )
                st.plotly_chart(fig_recurring_bar, use_container_width=True)

        st.markdown("---")

        # Purchaser Analytics (if purchaser data exists)
        st.markdown("### Spending by Purchaser")

        if 'purchaser' in df_invoices.columns:
            # Filter out None/null purchasers
            df_with_purchaser = df_invoices[df_invoices['purchaser'].notna() & (df_invoices['purchaser'] != '')]

            if not df_with_purchaser.empty:
                purchaser_stats = df_with_purchaser.groupby('purchaser').agg({
                    'total_amount': 'sum',
                    'id': 'count'
                }).reset_index()
                purchaser_stats.columns = ['purchaser', 'total_spent', 'invoice_count']
                purchaser_stats = purchaser_stats.sort_values('total_spent', ascending=False)

                col1, col2 = st.columns(2)

                with col1:
                    # Bar chart of spending by purchaser
                    fig_purchaser = ChartBuilder.create_colored_bar_chart(
                        data=purchaser_stats,
                        x='purchaser',
                        y='total_spent',
                        title='Spending by Purchaser',
                        color_by='total_spent',
                        color_scale='Greens'
                    )
                    st.plotly_chart(fig_purchaser, use_container_width=True)

                with col2:
                    # Pie chart for purchaser distribution
                    fig_purchaser_pie = ChartBuilder.create_pie_chart(
                        data=purchaser_stats,
                        values='total_spent',
                        names='purchaser',
                        title='Spending Distribution by Purchaser'
                    )
                    st.plotly_chart(fig_purchaser_pie, use_container_width=True)
            else:
                st.info("No purchaser information available in invoices.")

    else:
        st.info("No invoice data available for category analytics.")

    st.markdown("---")

    # Category breakdown (if categories exist)
    st.markdown("### Vendor Categories")

    vendors_full = asyncio.run(get_vendors())
    if vendors_full['vendors']:
        df_all_vendors = pd.DataFrame(vendors_full['vendors'])

        # Count by category
        if 'category' in df_all_vendors.columns:
            category_stats = df_all_vendors.groupby('category').agg({
                'total_spent': 'sum',
                'invoice_count': 'sum'
            }).reset_index()

            col1, col2 = st.columns(2)

            with col1:
                fig_cat = ChartBuilder.create_pie_chart(
                    data=category_stats,
                    values='total_spent',
                    names='category',
                    title='Spending by Category'
                )
                st.plotly_chart(fig_cat, use_container_width=True)

            with col2:
                fig_cat_bar = ChartBuilder.create_category_bar_chart(
                    data=category_stats,
                    x='category',
                    y='invoice_count',
                    title='Invoice Count by Category',
                    color_by='category'
                )
                st.plotly_chart(fig_cat_bar, use_container_width=True)

except Exception as e:
    st.error(f"Error loading analytics: {e}")
    st.info("Make sure the FastAPI server is running and you have uploaded some invoices.")
