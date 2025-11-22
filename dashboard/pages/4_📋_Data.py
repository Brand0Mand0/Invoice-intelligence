import streamlit as st
import asyncio
import pandas as pd
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import get_invoices, get_vendors, export_csv_url

# Add app directory to path to import formatters
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
from app.utils.formatters import format_currency

st.set_page_config(page_title="Data Browser", page_icon="📋", layout="wide")

st.title("📋 Data Browser")
st.markdown("Browse, search, and export your invoice data.")

# Tabs for different views
tab1, tab2 = st.tabs(["📄 Invoices", "🏢 Vendors"])

with tab1:
    st.markdown("### Invoice Data")

    try:
        invoices_data = asyncio.run(get_invoices())
        invoices = invoices_data.get("invoices", [])

        if invoices:
            st.info(f"Total Invoices: {invoices_data.get('total', 0)}")

            # Convert to DataFrame
            df = pd.DataFrame(invoices)

            # Add search
            search = st.text_input("🔍 Search invoices (vendor, invoice number, etc.)")

            if search:
                mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                df = df[mask]

            # Format currency
            df['total_amount'] = df['total_amount'].apply(format_currency)

            # Display table with new business intelligence fields
            st.dataframe(
                df[[
                    'vendor_normalized',
                    'invoice_number',
                    'date',
                    'total_amount',
                    'category',
                    'purchaser',
                    'is_recurring',
                    'parser_used',
                    'confidence_score'
                ]],
                column_config={
                    "vendor_normalized": "Vendor",
                    "invoice_number": "Invoice #",
                    "date": "Date",
                    "total_amount": "Amount",
                    "category": "Category",
                    "purchaser": "Purchaser",
                    "is_recurring": st.column_config.CheckboxColumn(
                        "Recurring",
                        help="Subscription or recurring charge"
                    ),
                    "parser_used": "Parser",
                    "confidence_score": st.column_config.NumberColumn(
                        "Confidence",
                        format="%.2f"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            # Export button
            st.markdown("### Export Data")
            st.markdown(f"[📥 Download CSV]({export_csv_url()})")

        else:
            st.info("No invoices found. Upload invoices to see data here.")

    except Exception as e:
        st.error(f"Error loading invoices: {e}")

with tab2:
    st.markdown("### Vendor Data")

    try:
        vendors_data = asyncio.run(get_vendors())
        vendors = vendors_data.get("vendors", [])

        if vendors:
            # Convert to DataFrame
            df_vendors = pd.DataFrame(vendors)

            # Add search
            search_vendor = st.text_input("🔍 Search vendors")

            if search_vendor:
                mask = df_vendors['normalized_name'].str.contains(search_vendor, case=False)
                df_vendors = df_vendors[mask]

            # Format currency
            df_vendors['total_spent'] = df_vendors['total_spent'].apply(format_currency)

            # Sort by total spent
            df_vendors = df_vendors.sort_values('invoice_count', ascending=False)

            # Display table
            st.dataframe(
                df_vendors[[
                    'normalized_name',
                    'category',
                    'total_spent',
                    'invoice_count',
                    'first_seen',
                    'last_seen'
                ]],
                column_config={
                    "normalized_name": "Vendor",
                    "category": "Category",
                    "total_spent": "Total Spent",
                    "invoice_count": "Invoices",
                    "first_seen": "First Seen",
                    "last_seen": "Last Seen"
                },
                hide_index=True,
                use_container_width=True
            )

            # Vendor stats
            st.markdown("### Vendor Statistics")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Vendors", len(vendors))

            with col2:
                categories = df_vendors['category'].nunique()
                st.metric("Categories", categories)

            with col3:
                avg_invoices = df_vendors['invoice_count'].mean() if 'invoice_count' in df_vendors else 0
                st.metric("Avg Invoices/Vendor", f"{avg_invoices:.1f}")

        else:
            st.info("No vendors found. Upload invoices to see vendor data here.")

    except Exception as e:
        st.error(f"Error loading vendors: {e}")
