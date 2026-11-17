
import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


# Fetch free models
@st.cache_data(ttl=3600)
def get_free_models():

    url = f"{BASE_URL}/models"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    models = response.json().get("data", [])

    free_models = []

    for model in models:

        model_id = model.get("id", "")
        pricing = model.get("pricing", {})

        if model_id.endswith(":free"):

            free_models.append({
                "id": model_id,
                "name": model.get("name", model_id),
                "pricing": pricing
            })

    return sorted(
        free_models,
        key=lambda x: x["name"].lower()
    )


# Generate AI response
def generate_response(messages, model):

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1500
    }

    response = requests.post(
        url,
        json=payload,
        headers=HEADERS,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"]


# Streamlit configuration
st.set_page_config(
    page_title="OpenRouter Chat",
    page_icon="😍",
    layout="wide"
)

st.title("❤️ OpenRouter Chat ❤️")
st.caption("A simple chatbot using OpenRouter API")


# Check API key
if not API_KEY:
    st.error("API Key is missing. Please set it in the .env file.")
    st.stop()


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []


# Sidebar settings
st.sidebar.header("⚙️ Settings")

try:

    models = get_free_models()

    model_options = {
        "Auto - OpenRouter Free Router":
            "/openrouter/free"
    }

    for model in models:

        model_options[
            f'{model["name"]} ({model["id"]})'
        ] = model["id"]

    selected_name = st.sidebar.selectbox(
        "Select a model",
        list(model_options.keys())
    )

    selected_model = model_options[selected_name]

    st.sidebar.success(
        f"Selected model: {selected_model}"
    )

except requests.RequestException as error:

    st.sidebar.error(f"Error fetching models: {error}")

    selected_model = "/openrouter/free"


# Clear conversation
if st.sidebar.button("Clear conversation"):

    st.session_state.messages = []
    st.rerun()


# Display previous conversation
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
if prompt := st.chat_input("Type your message..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    try:

        with st.chat_message("assistant"):

            with st.spinner("🤔 Thinking..."):

                answer = generate_response(
                    st.session_state.messages,
                    selected_model
                )

            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except requests.RequestException as error:

        st.error(f"Could not get a response: {error}")

    except (KeyError, IndexError, TypeError, ValueError) as error:

        st.error(f"Unexpected API response: {error}")
