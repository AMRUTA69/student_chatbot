# Requirements Document

## Introduction

A web-based academic student chatbot built with Python and Streamlit. Students enter a Google Gemini API key to activate the chatbot, then ask academic questions across any subject and receive AI-generated answers. The chatbot maintains multi-turn conversation history within the session, offers sidebar topic suggestions that pre-fill the input box, and handles errors gracefully.

## Glossary

- **App**: The Streamlit web application hosting the student chatbot.
- **Chatbot**: The AI-powered conversational component that answers academic questions using the Google Gemini API.
- **API Key**: A Google Gemini API key supplied by the student at runtime, stored only in session state and never persisted to disk.
- **Session**: A single browser session; all state is cleared on page refresh.
- **Conversation History**: The ordered list of user and assistant messages exchanged during a session, stored in `st.session_state`.
- **Topic Suggestion**: A clickable shortcut in the sidebar that pre-fills the chat input box with a suggested academic question stem.
- **Gemini Client**: The Google Generative AI SDK client instantiated with the student's API key.
- **Chat Input Box**: The Streamlit input widget at the bottom of the chat interface where students type their messages.

## Requirements

### Requirement 1 — API Key Entry

**User Story:** As a student, I want to enter my Google Gemini API key in the app, so that I can activate the chatbot without modifying any code.

#### Acceptance Criteria

1. THE App SHALL display an API key input field at the top of the main page before any chat interface is shown.
2. WHEN the student submits a non-empty string in the API key input field, THE App SHALL store the key in `st.session_state` for the duration of the session.
3. WHILE the API key field is empty or has not been submitted, THE App SHALL display a prompt instructing the student to enter their Gemini API key and SHALL NOT render the chat interface.
4. IF the page is refreshed or the session ends, THEN THE App SHALL clear the stored API key from `st.session_state`, requiring the student to re-enter it.

---

### Requirement 2 — Chatbot Activation

**User Story:** As a student, I want the chatbot to become active immediately after I enter my API key, so that I can start asking questions without any additional setup.

#### Acceptance Criteria

1. WHEN a valid-format API key is stored in `st.session_state`, THE App SHALL render the full chat interface, including the conversation history display and the Chat Input Box.
2. THE App SHALL instantiate the Gemini Client using the stored API key at the time the first message is sent.
3. WHEN the Gemini Client is instantiated, THE App SHALL use the `gemini-1.5-flash` model.

---

### Requirement 3 — Academic Question Answering

**User Story:** As a student, I want to ask academic questions on any subject and receive AI-generated answers, so that I can get help with my studies.

#### Acceptance Criteria

1. WHEN the student submits a message via the Chat Input Box, THE Chatbot SHALL send the message along with the full Conversation History to the Gemini API and display the response in the chat interface.
2. THE Chatbot SHALL accept academic questions on any subject without restricting topics.
3. WHEN the Gemini API returns a response, THE App SHALL append both the student's message and the assistant's response to the Conversation History in `st.session_state`.
4. WHEN a response is received, THE App SHALL display the student's message with a user avatar and the assistant's response with an assistant avatar in chronological order.

---

### Requirement 4 — Multi-Turn Conversation History

**User Story:** As a student, I want the chatbot to remember our conversation within a session, so that follow-up questions are answered in context.

#### Acceptance Criteria

1. THE App SHALL initialize an empty Conversation History list in `st.session_state` when a session starts.
2. WHEN a new message pair (user + assistant) is added, THE App SHALL append it to the existing Conversation History so that all prior messages are retained for the duration of the session.
3. WHEN sending a request to the Gemini API, THE Chatbot SHALL include the complete Conversation History as context so that the model can answer follow-up questions correctly.
4. THE App SHALL display the full Conversation History on every page render, with messages in the order they were exchanged.

---

### Requirement 5 — Sidebar Topic Suggestions

**User Story:** As a student, I want quick topic suggestions in the sidebar, so that I can easily start asking about common academic subjects.

#### Acceptance Criteria

1. THE App SHALL display a sidebar containing a labeled list of clickable Topic Suggestion buttons covering a range of academic subjects.
2. WHEN the student clicks a Topic Suggestion button, THE App SHALL pre-fill the Chat Input Box with the corresponding question stem so the student can edit it before sending.
3. THE App SHALL provide at least six Topic Suggestions spanning different academic disciplines (e.g., Mathematics, Science, History, Literature, Programming, General Study Tips).

---

### Requirement 6 — Clear Chat

**User Story:** As a student, I want to clear the conversation history, so that I can start a fresh chat session without refreshing the page.

#### Acceptance Criteria

1. THE App SHALL display a "Clear Chat" button in the sidebar.
2. WHEN the student clicks the "Clear Chat" button, THE App SHALL reset the Conversation History in `st.session_state` to an empty list.
3. WHEN the Conversation History is cleared, THE App SHALL immediately re-render the chat interface showing no previous messages.

---

### Requirement 7 — Error Handling

**User Story:** As a student, I want the app to handle errors gracefully, so that I understand what went wrong without the app crashing.

#### Acceptance Criteria

1. IF the Gemini API returns an authentication error (e.g., invalid or expired API key), THEN THE App SHALL display a clear error message informing the student that the API key is invalid and SHALL NOT add any incomplete message pair to the Conversation History.
2. IF the Gemini API returns a network or service error, THEN THE App SHALL display a descriptive error message to the student and SHALL NOT crash or display a raw exception traceback.
3. IF the student submits an empty message, THEN THE App SHALL NOT send a request to the Gemini API and SHALL NOT modify the Conversation History.
4. WHEN an error occurs during an API call, THE App SHALL preserve the existing Conversation History so the student can continue the session after resolving the issue.
