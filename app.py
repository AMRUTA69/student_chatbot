"""
Academic Student Chatbot
A Streamlit app powered by Google Gemini (gemini-2.5-flash).

Usage:
    streamlit run app.py

The Gemini API key is read from Streamlit secrets (GEMINI_API_KEY) when
available, so it does not have to be typed every time. If no secret is
set, the app asks the student to enter their own key. Conversation
history is maintained for the duration of the browser session.
"""

import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPIError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOPIC_SUGGESTIONS = [
    ("Mathematics",        "Explain the concept of "),
    ("Science",            "Describe the process of "),
    ("History",            "What were the main causes of "),
    ("Literature",         "Analyse the themes in "),
    ("Programming",        "How does "),
    ("General Study Tips", "What are effective strategies for "),
]


# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------

def get_default_api_key():
    """Read the key from Streamlit secrets if available."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

def init_session_state():
    """Initialise required session_state keys on first run."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = get_default_api_key()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "prefill" not in st.session_state:
        st.session_state.prefill = None


# ---------------------------------------------------------------------------
# API Key Gate
# ---------------------------------------------------------------------------

def render_api_key_gate():
    """
    Render the API key input UI.

    Returns True when a key is already stored in session state so the
    caller can proceed to render the chat interface.  Returns False and
    renders the key-entry form when no key is present.
    """
    if st.session_state.api_key:
        return True

    st.info(
        "Enter your Google Gemini API key below to activate the chatbot. "
        "The key is stored only for this browser session and is never saved to disk."
    )

    key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        key="api_key_input",
    )

    if st.button("Activate Chatbot", type="primary"):
        if key.strip():
            st.session_state.api_key = key.strip()
            st.rerun()
        else:
            st.warning("API key cannot be empty.")

    return False


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """
    Render the sidebar with topic suggestion buttons and the Clear Chat button.

    Clicking a topic button pre-fills the chat input with a question stem;
    it does NOT auto-send the message.
    """
    with st.sidebar:
        st.header("Topic Suggestions")
        st.caption("Click a topic to pre-fill the chat input.")

        for label, stem in TOPIC_SUGGESTIONS:
            if st.button(label, use_container_width=True, key="topic_" + label):
                st.session_state.prefill = stem
                st.rerun()

        st.divider()

        if st.button("Clear Chat", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()


# ---------------------------------------------------------------------------
# Gemini API Caller
# ---------------------------------------------------------------------------

def call_gemini(api_key, messages):
    """
    Send the conversation to the Gemini API and return the assistant reply.

    Args:
        api_key:  The Gemini API key.
        messages: Full conversation history including the latest user message
                  as the last entry.  Each entry has keys 'role' and 'content'.

    Returns:
        The assistant reply text on success, or None on any error.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # Updated from gemini-1.5-flash, which was retired by Google.
            system_instruction=(
                "You are a knowledgeable and friendly academic tutor. "
                "Help students understand concepts clearly, provide accurate "
                "explanations, and encourage curiosity across all academic subjects."
            ),
        )

        # Build history for the SDK (all messages except the current one).
        # The Gemini SDK uses "model" for the assistant role.
        history = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [m["content"]],
            }
            for m in messages[:-1]
        ]

        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text

    except PermissionDenied:
        st.error(
            "Invalid or expired API key. "
            "Please check the Gemini API key and try again."
        )
        return None

    except GoogleAPIError as exc:
        detail = getattr(exc, "message", str(exc))
        st.error("API error: " + detail)
        return None

    except Exception as exc:
        st.error("Unexpected error: " + str(exc))
        return None


# ---------------------------------------------------------------------------
# Message Handler
# ---------------------------------------------------------------------------

def handle_message(user_input):
    """
    Process a user message: update history, call Gemini, update history again.

    Uses an optimistic-append pattern:
    - The user message is appended to history immediately.
    - If the API call fails, the user message is popped so history is
      never left in an inconsistent state.

    Empty or whitespace-only inputs are silently ignored.
    """
    if not user_input.strip():
        return

    # Append and render the user message.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call the API and render the assistant reply.
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = call_gemini(
                api_key=st.session_state.api_key,
                messages=st.session_state.messages,
            )

    if response_text is not None:
        # Success: persist the assistant message and re-render.
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()
    else:
        # Error: roll back the optimistically-appended user message.
        st.session_state.messages.pop()


# ---------------------------------------------------------------------------
# Chat Interface
# ---------------------------------------------------------------------------

def render_chat():
    """
    Render the full conversation history and the chat input widget.

    If a topic suggestion was clicked in the sidebar, its stem is used as
    the placeholder text in the chat input box.
    """
    # Display all past messages in chronological order.
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Consume the pending pre-fill stem (if any) as the input placeholder.
    placeholder = st.session_state.prefill or "Ask an academic question..."
    st.session_state.prefill = None

    # Capture new input and process it.
    if user_input := st.chat_input(placeholder):
        handle_message(user_input.strip())


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    """Wire all components together and run the app."""
    st.set_page_config(
        page_title="Academic Student Chatbot",
        page_icon="\U0001F393",
        layout="centered",
    )
    st.title("Academic Student Chatbot")

    init_session_state()
    render_sidebar()

    # Gate: only render the chat interface once the API key is available.
    if not render_api_key_gate():
        st.stop()

    render_chat()


if __name__ == "__main__":
    main()