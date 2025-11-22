import streamlit as st
import asyncio
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import send_chat_query, get_chat_history

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

st.title("💬 AI Chat Interface")
st.markdown("Ask natural language questions about your invoices. Powered by **NEAR AI DeepSeek-V3.1** with TEE attestation.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load chat history from database on first load
if "loaded_history" not in st.session_state:
    try:
        history_data = asyncio.run(get_chat_history(limit=10))
        conversations = history_data.get("conversations", [])

        # Add to session state (reverse to show oldest first)
        for conv in reversed(conversations):
            st.session_state.messages.append({
                "role": "user",
                "content": conv["query"]
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": conv["response"],
                "completion_id": conv.get("completion_id")
            })

        st.session_state.loaded_history = True
    except Exception as e:
        st.session_state.loaded_history = True
        st.warning(f"Could not load chat history: {e}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show TEE attestation for assistant messages
        if message["role"] == "assistant" and "completion_id" in message:
            completion_id = message.get("completion_id")
            if completion_id:
                st.caption(f"🔒 **TEE attested response**")
                st.caption(f"Completion ID: `{completion_id}`")
            else:
                st.caption("⚠️ TEE completion ID not available")

# Chat input
if prompt := st.chat_input("Ask a question about your invoices..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            response_data = asyncio.run(send_chat_query(prompt))

            # Display response
            message_placeholder.markdown(response_data["response"])

            # Show TEE attestation with completion ID
            completion_id = response_data.get("completion_id")
            if completion_id:
                st.caption(f"🔒 **TEE attested response**")
                st.caption(f"Completion ID: `{completion_id}`")
            else:
                st.caption("⚠️ TEE completion ID not available")

            # Add to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_data["response"],
                "completion_id": completion_id
            })

        except Exception as e:
            message_placeholder.markdown(f"❌ Error: {str(e)}")
            st.error("Make sure the FastAPI server is running and you have uploaded some invoices.")

st.markdown("---")

# Suggested queries
st.markdown("### Suggested Queries")

col1, col2, col3 = st.columns(3)

# Helper function to process suggested queries
def process_suggested_query(query_text):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query_text
    })

    # Get AI response
    try:
        response_data = asyncio.run(send_chat_query(query_text))

        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_data["response"],
            "completion_id": response_data.get("completion_id")
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Error: {str(e)}"
        })

with col1:
    if st.button("📊 What are my top 5 vendors?"):
        process_suggested_query("What are my top 5 vendors?")
        st.rerun()

with col2:
    if st.button("📈 Show spending trend"):
        process_suggested_query("Show me my spending trend for the last 6 months")
        st.rerun()

with col3:
    if st.button("💰 Total spending"):
        process_suggested_query("What is my total spending across all invoices?")
        st.rerun()

# Clear chat button
if st.button("🗑️ Clear Chat History", type="secondary"):
    st.session_state.messages = []
    st.rerun()

st.markdown("---")

st.markdown("""
### About AI Chat

This chat interface uses **NEAR AI DeepSeek-V3.1** to answer questions about your invoice data.
The AI has access to:
- All invoices and their details
- Vendor information and spending patterns
- Monthly trends and statistics

Every response includes a **TEE (Trusted Execution Environment) attestation** for verification and trust.
""")
