# Design Document

## Overview

The student chatbot is a single-file Streamlit application (`app.py`) that wraps the Google Generative AI Python SDK. Students supply their own Gemini API key at runtime; the app gates the chat interface behind that key, maintains multi-turn conversation history in `st.session_state`, and provides sidebar shortcuts for common academic topics.

---

## Architecture

The application follows a straightforward single-page Streamlit architecture with no persistent backend. All state lives in `st.session_state` for the lifetime of the browser session.

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit App (app.py)              │
│                                                     │
│  ┌──────────────┐        ┌────────────────────────┐ │
│  │   Sidebar    │        │      Main Area         │ │
│  │              │        │                        │ │
│  │ Topic buttons│        │  API Key Input  ──┐    │ │
│  │ Clear Chat   │        │                   │    │ │
│  └──────────────┘        │  Chat Interface   │    │ │
│                          │  (after key set)  │    │ │
│                          └────────────────────────┘ │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              st.session_state                │   │
│  │  api_key: str | None                         │   │
│  │  messages: list[dict]  ← conversation history│   │
│  │  prefill: str | None   ← topic suggestion    │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │           GeminiClient (wrapper)             │   │
│  │  - Instantiated on first message send        │   │
│  │  - Model: gemini-1.5-flash                   │   │
│  │  - Sends full conversation history           │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
             Google Generative AI API
```

---

## Components

### 1. Session State Initializer

Runs at the top of every page render. Ensures required keys exist in `st.session_state` without overwriting existing values.

```python
def init_session_state():
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "prefill" not in st.session_state:
        st.session_state.prefill = None
```

### 2. API Key Gate

Renders the API key input field. Returns `True` when a key is stored, `False` otherwise.

```python
def render_api_key_gate() -> bool:
    if st.session_state.api_key:
        return True
    st.info("Please enter your Google Gemini API key to start chatting.")
    key = st.text_input("Gemini API Key", type="password", key="api_key_input")
    if st.button("Activate Chatbot"):
        if key.strip():
            st.session_state.api_key = key.strip()
            st.rerun()
        else:
            st.warning("API key cannot be empty.")
    return False
```

### 3. Sidebar

Renders topic suggestion buttons and the Clear Chat button.

```python
TOPIC_SUGGESTIONS = [
    ("Mathematics", "Explain the concept of "),
    ("Science", "Describe the process of "),
    ("History", "What were the main causes of "),
    ("Literature", "Analyse the themes in "),
    ("Programming", "How does "),
    ("General Study Tips", "What are effective strategies for "),
]

def render_sidebar():
    with st.sidebar:
        st.header("Topic Suggestions")
        for label, stem in TOPIC_SUGGESTIONS:
            if st.button(label, use_container_width=True):
                st.session_state.prefill = stem
                st.rerun()

        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
```

### 4. Chat Interface

Renders conversation history and the chat input widget.

```python
def render_chat():
    # Display conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Pre-fill from topic suggestion if set
    placeholder = st.session_state.prefill or "Ask an academic question..."
    st.session_state.prefill = None  # consume after use

    if user_input := st.chat_input(placeholder):
        handle_message(user_input.strip())
```

### 5. Message Handler

Validates input, calls the Gemini API, and updates conversation history.

```python
def handle_message(user_input: str):
    if not user_input:
        return  # empty input guard

    # Append user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Call Gemini API with full history
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = call_gemini(
                api_key=st.session_state.api_key,
                messages=st.session_state.messages,
            )

    if response_text is not None:
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()
    else:
        # Remove the optimistically-appended user message on error
        st.session_state.messages.pop()
```

### 6. Gemini API Caller

Isolated function that wraps the Google Generative AI SDK. Returns `None` on error and displays a user-friendly message.

```python
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied, GoogleAPIError

def call_gemini(api_key: str, messages: list[dict]) -> str | None:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Convert message history to Gemini SDK format
        history = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in messages[:-1]  # exclude last (the current user message)
        ]
        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text

    except PermissionDenied:
        st.error("❌ Invalid or expired API key. Please re-enter your Gemini API key.")
        return None
    except GoogleAPIError as e:
        st.error(f"⚠️ API error: {e.message}")
        return None
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {str(e)}")
        return None
```

---

## Data Models

### Message

A dictionary stored in `st.session_state.messages`:

```python
{
    "role": "user" | "assistant",   # str — identifies the speaker
    "content": str                  # the message text
}
```

### Session State Schema

```python
{
    "api_key":  str | None,         # Gemini API key; None before entry
    "messages": list[Message],      # ordered conversation history
    "prefill":  str | None          # pending topic-suggestion stem
}
```

---

## Interfaces

### External: Google Generative AI SDK

- **Package**: `google-generativeai`
- **Configuration**: `genai.configure(api_key=<key>)`
- **Model**: `gemini-1.5-flash`
- **Chat API**: `model.start_chat(history=[...])` → `chat.send_message(text)`
- **History format**: `[{"role": "user"|"model", "parts": ["text"]}]`
  - Note: Gemini SDK uses `"model"` for assistant role; map `"assistant"` → `"model"` when building history.

### Internal: Function Contracts

| Function | Input | Output | Side Effects |
|---|---|---|---|
| `init_session_state()` | — | — | Initializes `st.session_state` keys |
| `render_api_key_gate()` | — | `bool` | Renders Streamlit UI; may set `st.session_state.api_key` |
| `render_sidebar()` | — | — | Renders sidebar; may set `st.session_state.prefill` or clear messages |
| `render_chat()` | — | — | Renders chat history and input widget |
| `handle_message(str)` | `user_input: str` | — | Appends to `st.session_state.messages`; calls `call_gemini` |
| `call_gemini(str, list)` | `api_key`, `messages` | `str \| None` | Calls Gemini API; renders error via `st.error` on failure |

---

## Application Entry Point

```python
def main():
    st.set_page_config(page_title="Academic Student Chatbot", page_icon="🎓")
    st.title("🎓 Academic Student Chatbot")

    init_session_state()
    render_sidebar()

    if not render_api_key_gate():
        st.stop()

    render_chat()

if __name__ == "__main__":
    main()
```

---

## Error Handling Strategy

| Error Condition | Detection | Response |
|---|---|---|
| Empty API key submission | `key.strip()` is falsy | Show warning; do not store |
| Empty chat message | `user_input.strip()` is falsy | Return early; no API call |
| Invalid / expired API key | `google.api_core.exceptions.PermissionDenied` | `st.error(...)`, remove optimistic user message, history unchanged |
| Network / service error | `GoogleAPIError` subclasses | `st.error(...)`, remove optimistic user message, history unchanged |
| Unexpected exception | Bare `Exception` | `st.error(...)`, remove optimistic user message, history unchanged |

The optimistic-append pattern (append user message first, remove on error) ensures the history is never left with a dangling user message that has no assistant reply.

---

## Project Structure

```
student-chatbot/
├── app.py               # Single-file Streamlit application
├── requirements.txt     # Python dependencies
└── .kiro/
    └── specs/
        └── student-chatbot/
            ├── requirements.md
            └── design.md
```

### requirements.txt

```
streamlit>=1.35.0
google-generativeai>=0.7.0
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Non-empty API key is stored in session state

*For any* non-empty string submitted as an API key, the value stored in `st.session_state.api_key` after submission SHALL equal that string.

**Validates: Requirements 1.2**

---

### Property 2: Conversation history grows by exactly one pair per exchange

*For any* conversation history of arbitrary length, after a successful user message and assistant response cycle, the history SHALL contain exactly two more entries than before (one user message and one assistant message), and all prior entries SHALL remain unchanged.

**Validates: Requirements 3.3, 4.2**

---

### Property 3: Full conversation history is included in every API call

*For any* conversation history, when a new user message is sent, the payload delivered to the Gemini API SHALL contain all prior messages in their original order followed by the new user message.

**Validates: Requirements 3.1, 4.3**

---

### Property 4: All messages are rendered in chronological order with correct avatars

*For any* conversation history of any length, rendering the chat interface SHALL display every message exactly once, in insertion order, with user messages assigned a `"user"` avatar and assistant messages assigned an `"assistant"` avatar.

**Validates: Requirements 3.4, 4.4**

---

### Property 5: Topic suggestion pre-fills the input stem exactly

*For any* topic suggestion button click, the value placed into `st.session_state.prefill` SHALL equal the predefined question stem associated with that topic button.

**Validates: Requirements 5.2**

---

### Property 6: Clear chat resets history to empty regardless of prior state

*For any* non-empty conversation history, clicking "Clear Chat" SHALL set `st.session_state.messages` to an empty list.

**Validates: Requirements 6.2**

---

### Property 7: Errors during API calls preserve existing conversation history

*For any* conversation history and any API error (authentication, network, or unexpected), after the error is handled the conversation history SHALL be identical to its state before the failed request was initiated.

**Validates: Requirements 7.1, 7.4**

---

### Property 8: Empty or whitespace-only messages are rejected without side effects

*For any* conversation history and any message string composed entirely of whitespace (including the empty string), submitting that message SHALL NOT modify the conversation history and SHALL NOT invoke the Gemini API.

**Validates: Requirements 7.3**
