import streamlit as st
import asyncio
import time
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import upload_pdf, get_job_status

st.set_page_config(page_title="Upload Invoices", page_icon="📤", layout="wide")

st.title("📤 Upload Invoices")
st.markdown("Upload PDF invoices for processing through our AI-powered extraction pipeline.")

# File uploader - SUPPORTS MULTIPLE FILES
uploaded_files = st.file_uploader(
    "Choose PDF invoice(s)",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload one or more PDF invoices to extract vendor, amount, and line item data"
)

if uploaded_files:
    st.info(f"📄 **{len(uploaded_files)} file(s) selected** - Total size: {sum(f.size for f in uploaded_files) / 1024:.1f} KB")

    # Show file list
    with st.expander("View selected files"):
        for f in uploaded_files:
            st.write(f"- {f.name} ({f.size / 1024:.1f} KB)")

    if st.button(f"🚀 Process {len(uploaded_files)} Invoice(s)", type="primary"):
        st.markdown(f"### Processing {len(uploaded_files)} Invoice(s)")

        # Create containers for overall progress
        overall_progress = st.progress(0)
        overall_status = st.empty()

        job_ids = []
        results_summary = []

        # Step 1: Upload all files
        overall_status.info("📤 Uploading files...")
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                file_bytes = uploaded_file.read()
                result = asyncio.run(upload_pdf(file_bytes, uploaded_file.name))
                job_ids.append((uploaded_file.name, result["job_id"]))
                overall_progress.progress((idx + 1) / len(uploaded_files) * 0.3)  # 30% for upload
            except Exception as e:
                st.error(f"❌ Error uploading {uploaded_file.name}: {str(e)}")

        st.success(f"✅ All {len(job_ids)} files uploaded!")

        # Step 2: Monitor processing
        overall_status.info("⚙️ Processing invoices...")
        completed = 0
        max_attempts = 60

        for attempt in range(max_attempts):
            all_done = True

            for file_name, job_id in job_ids:
                try:
                    status_data = asyncio.run(get_job_status(job_id))
                    status = status_data["status"]

                    if status in ["queued", "processing"]:
                        all_done = False
                    elif status == "complete":
                        if job_id not in [r["job_id"] for r in results_summary]:
                            completed += 1
                            results_summary.append({
                                "filename": file_name,
                                "job_id": job_id,
                                "result": status_data.get("result", {})
                            })
                            overall_progress.progress(0.3 + (completed / len(job_ids)) * 0.7)
                    elif status == "error":
                        if job_id not in [r["job_id"] for r in results_summary]:
                            completed += 1
                            results_summary.append({
                                "filename": file_name,
                                "job_id": job_id,
                                "error": status_data.get("error", "Unknown error")
                            })
                            overall_progress.progress(0.3 + (completed / len(job_ids)) * 0.7)
                except Exception as e:
                    st.error(f"❌ Error checking status for {file_name}: {str(e)}")

            if all_done:
                break

            overall_status.info(f"⚙️ Processing... {completed}/{len(job_ids)} complete")
            time.sleep(2)

        # Step 3: Display results
        overall_status.success(f"✅ Processing complete! {completed}/{len(job_ids)} invoices processed")
        overall_progress.progress(1.0)

        st.markdown("### Results Summary")

        # Show successful results
        successful = [r for r in results_summary if "result" in r]
        failed = [r for r in results_summary if "error" in r]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Successful", len(successful))
        with col2:
            st.metric("❌ Failed", len(failed))

        # Show details for each
        for result in successful:
            with st.expander(f"✅ {result['filename']}", expanded=False):
                result_data = result["result"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Parser", result_data.get("parser_used", "N/A"))
                with col2:
                    st.metric("Confidence", f"{result_data.get('confidence', 0) * 100:.0f}%")
                with col3:
                    st.metric("Vendor", result_data.get("vendor", "N/A"))

        for result in failed:
            with st.expander(f"❌ {result['filename']}", expanded=False):
                st.error(f"Error: {result['error']}")

st.markdown("---")

# Show recent uploads
st.markdown("### Recent Processing Jobs")

try:
    # Get recent invoices to show
    from db_utils import get_invoices
    invoices_data = asyncio.run(get_invoices())
    invoices = invoices_data.get("invoices", [])

    if invoices:
        # Show last 5 invoices
        recent = invoices[:5]

        for inv in recent:
            with st.expander(f"{inv['vendor_normalized']} - ${inv['total_amount']:.2f} ({inv['date']})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Invoice #:** {inv.get('invoice_number', 'N/A')}")
                    st.write(f"**Vendor:** {inv['vendor_name']}")
                with col2:
                    st.write(f"**Date:** {inv['date']}")
                    st.write(f"**Amount:** ${inv['total_amount']:.2f}")
                with col3:
                    st.write(f"**Parser:** {inv['parser_used']}")
                    st.write(f"**Confidence:** {inv['confidence_score'] * 100 if inv['confidence_score'] else 0:.0f}%")
    else:
        st.info("No invoices processed yet. Upload your first invoice above!")

except Exception as e:
    st.error(f"Error loading recent invoices: {e}")

st.markdown("---")
st.markdown("""
### Processing Pipeline

Our multi-tier extraction pipeline:
1. **pdfplumber** - Fast extraction for structured PDFs (~90% confidence)
2. **invoice2data** - Template-based fallback (~85% confidence)
3. **NEAR AI DeepSeek** - AI-powered final fallback (~95% confidence)

All results are cached to prevent re-processing.
""")
