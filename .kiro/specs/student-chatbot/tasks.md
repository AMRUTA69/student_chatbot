# Implementation Plan: Student Chatbot

## Overview

Build a single-file Streamlit application (`app.py`) backed by the Google Generative AI SDK. The implementation proceeds in four stages: project scaffold → core session/UI components → Gemini integration and error handling → wiring everything together.

## Tasks

- [ ] 1. Set up project scaffold
  - [ ] 1.1 Create `requirements.txt` with pinned dependencies
    - Add `streamlit>=1.35.0` and `google-generativeai>=0.7.0`
    - _Requirements: implicitly required for all features_

  - [ ] 1.2 Create `app.py` with imports, constants, and `init_session_state()`
    - Import `streamlit`, `google.generativeai`, and exception types
    - Define `TOPIC_SUGGESTIONS` list with at least six entries covering Mathematics, Science, History, Literature, Programming, and General Study Tips
    - Implement `init_session_state()` that initialises `api_key`, `messages`, and `prefill` in `st.session_state` only if the keys are absent
    - _Requirements: 1.4, 4.1, 5.3_

- [ ] 2. Implement API key gate
  - [ ] 2.1 Implement `render_api_key_gate()` function
    - Return `True` immediately if `st.session_state.api_key` is already set
    - Display an info prompt telling the student to enter their key
    - Render a password-type text input and an "Activate Chatbot" button
    - On button click, strip and validate the input: store in `st.session_state.api_key` and call `st.rerun()` if non-empty; show a warning if empty
    - Return `False` when no key is stored
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.2 Write property test for API key storage (Property 1)
    - **Property 1: Non-empty API key is stored in session state**
    - Verify that for any non-empty string submitted, `st.session_state.api_key` equals that exact string after the gate logic runs
    - **Validates: Requirements 1.2**

- [ ] 3. Implement sidebar
  - [ ] 3.1 Implement `render_sidebar()` function
    - Render a "Topic Suggestions" header inside `st.sidebar`
    - Iterate over `TOPIC_SUGGESTIONS` and render one `st.button` per entry; on click, set `st.session_state.prefill` to the corresponding stem and call `st.rerun()`
    - Render a divider and a "🗑️ Clear Chat" button; on click, reset `st.session_state.messages` to `[]` and call `st.rerun()`
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3_

  - [ ]* 3.2 Write property test for topic suggestion pre-fill (Property 5)
    - **Property 5: Topic suggestion pre-fills the input stem exactly**
    - For each entry in `TOPIC_SUGGESTIONS`, simulate a button click and assert `st.session_state.prefill` equals the predefined stem
    - **Validates: Requirements 5.2**

  - [ ]* 3.3 Write property test for clear chat (Property 6)
    - **Property 6: Clear chat resets history to empty regardless of prior state**
    - For any non-empty `messages` list, simulate clicking "Clear Chat" and assert `st.session_state.messages == []`
    - **Validates: Requirements 6.2**

- [ ] 4. Checkpoint — Ensure scaffold and UI components are wired correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Gemini API caller
  - [ ] 5.1 Implement `call_gemini(api_key, messages)` function
    - Call `genai.configure(api_key=api_key)`
    - Instantiate `genai.GenerativeModel("gemini-1.5-flash")`
    - Build `history` from all messages except the last, mapping `"assistant"` role to `"model"` for the SDK
    - Start a chat session with `model.start_chat(history=history)` and send the last message via `chat.send_message(...)`
    - Return `response.text` on success
    - Catch `PermissionDenied` and display `st.error` with an invalid-key message; return `None`
    - Catch `GoogleAPIError` and display `st.error` with the error message; return `None`
    - Catch bare `Exception` and display `st.error` with the exception string; return `None`
    - _Requirements: 2.2, 2.3, 7.1, 7.2_

  - [ ]* 5.2 Write property test for full history inclusion in API call (Property 3)
    - **Property 3: Full conversation history is included in every API call**
    - Mock the Gemini SDK; for any history of arbitrary length, assert the payload sent to `chat.send_message` contains the new user message and that `start_chat` receives all prior messages in original order
    - **Validates: Requirements 3.1, 4.3**

  - [ ]* 5.3 Write property test for error handling preserving history (Property 7)
    - **Property 7: Errors during API calls preserve existing conversation history**
    - For each exception type (`PermissionDenied`, `GoogleAPIError`, `Exception`), assert that after the error is caught `st.session_state.messages` is unchanged from its pre-call state
    - **Validates: Requirements 7.1, 7.4**

- [ ] 6. Implement message handler and chat interface
  - [ ] 6.1 Implement `handle_message(user_input)` function
    - Return early without side effects if `user_input` is empty or whitespace-only
    - Append `{"role": "user", "content": user_input}` to `st.session_state.messages`
    - Render the user message in a `st.chat_message("user")` block
    - Inside an `st.chat_message("assistant")` block with `st.spinner`, call `call_gemini`
    - If the response is not `None`, append the assistant message and call `st.rerun()`
    - If the response is `None` (error path), pop the optimistically-appended user message to leave history unchanged
    - _Requirements: 3.1, 3.3, 7.1, 7.2, 7.3, 7.4_

  - [ ]* 6.2 Write property test for conversation history growth (Property 2)
    - **Property 2: Conversation history grows by exactly one pair per exchange**
    - Mock `call_gemini` to return a fixed string; for any initial history length, assert that after `handle_message` the history is exactly two entries longer and all prior entries are unchanged
    - **Validates: Requirements 3.3, 4.2**

  - [ ]* 6.3 Write property test for empty message rejection (Property 8)
    - **Property 8: Empty or whitespace-only messages are rejected without side effects**
    - For any whitespace-only or empty string, assert `handle_message` does not modify `st.session_state.messages` and does not invoke `call_gemini`
    - **Validates: Requirements 7.3**

  - [ ] 6.4 Implement `render_chat()` function
    - Iterate over `st.session_state.messages` and render each in a `st.chat_message` block with `st.markdown`
    - Read `st.session_state.prefill` as the placeholder; reset it to `None` after reading
    - Capture input from `st.chat_input` and call `handle_message` with the stripped value
    - _Requirements: 3.1, 3.4, 4.4, 5.2_

  - [ ]* 6.5 Write property test for chronological rendering (Property 4)
    - **Property 4: All messages rendered in chronological order with correct avatars**
    - For any list of alternating user/assistant messages, assert that `render_chat` renders each message exactly once in insertion order with the correct role
    - **Validates: Requirements 3.4, 4.4**

- [ ] 7. Wire everything together with `main()`
  - [ ] 7.1 Implement `main()` and the `__name__ == "__main__"` guard
    - Call `st.set_page_config(page_title="Academic Student Chatbot", page_icon="🎓")`
    - Call `st.title("🎓 Academic Student Chatbot")`
    - Call `init_session_state()`, then `render_sidebar()`
    - Call `render_api_key_gate()`; if it returns `False`, call `st.stop()` to halt rendering
    - Call `render_chat()` only when the gate passes
    - _Requirements: 1.1, 1.3, 2.1_

- [ ] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use `hypothesis` (or `pytest` with manual parameterisation) to verify universal correctness properties; unit tests use `pytest` with `unittest.mock` to mock the Gemini SDK and Streamlit session state
- The optimistic-append pattern in `handle_message` ensures the conversation history is never left in an inconsistent state after an API error
- The `"assistant"` → `"model"` role mapping must be applied when building the Gemini SDK history, since the SDK uses `"model"` while internal state uses `"assistant"`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "3.3", "5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "6.1"] },
    { "id": 4, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 5, "tasks": ["6.5", "7.1"] }
  ]
}
```
