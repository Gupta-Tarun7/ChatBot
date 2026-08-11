import streamlit as st
from langgraph_backend import chatbot,retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid


# =========================================================
# Utility Functions
# =========================================================

def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():
    new_thread_id = generate_thread_id()

    add_thread(st.session_state["thread_id"])

    st.session_state["thread_id"] = new_thread_id
    st.session_state["message_history"] = []


def load_conversation(thread_id):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = chatbot.get_state(config)

    if not state.values:
        return []

    return state.values.get("messages", [])


# =========================================================
# Session Setup
# =========================================================

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])


# =========================================================
# Sidebar UI
# =========================================================

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()


st.sidebar.header("Conversation")


for thread_id in st.session_state["chat_threads"][::-1]:

    if st.sidebar.button(str(thread_id)):

        st.session_state["thread_id"] = thread_id

        messages = load_conversation(thread_id)

        temp_message = []

        for msg in messages:

            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"

            content = msg.content

            if isinstance(content, list):

                text_parts = []

                for block in content:

                    if isinstance(block, dict):

                        text = block.get("text")

                        if text:
                            text_parts.append(text)

                content = "".join(text_parts)

            temp_message.append(
                {
                    "role": role,
                    "content": content
                }
            )

        st.session_state["message_history"] = temp_message

        st.rerun()


# =========================================================
# Main UI
# =========================================================

st.title("💬 LangGraph Chatbot")


for message in st.session_state["message_history"]:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# =========================================================
# Chat Input
# =========================================================

user_input = st.chat_input("Type here...")


if user_input:

    st.session_state["message_history"].append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.write(user_input)


    CONFIG = {
        "configurable": {
            "thread_id": st.session_state["thread_id"]
        }
    }


    with st.chat_message("assistant"):

        def generate_response():

            for message_chunk, metadata in chatbot.stream(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
                config=CONFIG,
                stream_mode="messages"
            ):

                content = message_chunk.content

                if isinstance(content, str):
                    yield content

                elif isinstance(content, list):

                    for block in content:

                        if isinstance(block, dict):

                            text = block.get("text")

                            if text:
                                yield text


        ai_message = st.write_stream(generate_response())


    st.session_state["message_history"].append(
        {
            "role": "assistant",
            "content": ai_message
        }
    )