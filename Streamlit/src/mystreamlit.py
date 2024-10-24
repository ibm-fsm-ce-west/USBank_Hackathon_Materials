import os
import streamlit as st
from datetime import datetime
from watsonxai import WatsonxAIWrapper
# Initialize session state for messages
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
    

st.set_page_config(page_title="Chat With Your XXX", page_icon="💬")

st.title("💬 Chat With Your XXX")

# You can comment out this function to call API 
def get_wxai_response(prompt):
    try:
        # watson = WatsonxAIWrapper()
        # return watson.call_wx_api(prompt) 
        return "Dummy reponse"
    except Exception as e:
        print(f'Error: {e}')
        return "Failure during call API"

# Display chat history
for message in st.session_state['messages']:
    if message['role'] == 'user':
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**watsonx:** {message['content']}")

# User input
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_input("You:", "")
    submit_button = st.form_submit_button(label='Send')

if submit_button and user_input:
    # Append user message
    st.session_state['messages'].append({"role": "user", "content": user_input})
    
    # Get response
    with st.spinner("watsonx is typing..."):
        response = get_wxai_response(user_input)
    
    # Append assistant response
    st.session_state['messages'].append({"role": "assistant", "content": response})
    
    # Rerun to update chat
    st.rerun()