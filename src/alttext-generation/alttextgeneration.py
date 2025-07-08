import streamlit as st
from PIL import Image
from openai import OpenAI
import io
import base64
import json
import time

from config import get_customer_settings

from utils import zip_to_jsonl
from batch import *


# Access the secret key
# openai.api_key = st.secrets["openai"]["api_key"]
# Initialize the OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

#get the client settings
customer_settings = get_customer_settings()
default_prompt = customer_settings['prompt']

st.title("Alt-Text Generator")

st.write(customer_settings["max_size_tuple"])

#input form 
with st.form(key="alttext_form"):
    tone_options = [
        "Inclusive",
        "Neutral",
        "Elegant",
        "Functional",
        "Minimalist",
        "Luxury",
        "SEO-Friendly",
        "Streetwear",
        "Playful",
        "Earthy",
        "Vintage",
        "Sporty",
        "Feminine",
        "Masculine",
        "Avant-garde",
        "Narrative",
        "Conversational",
    ]

    selected_tone = st.selectbox("Select a tone for the alt text", tone_options, index=2)

    uploaded_file = st.file_uploader("Upload an image",)# type=["png", "jpg", "jpeg"])

    subm = st.form_submit_button("Generate Alt Text")

if subm and uploaded_file:

    submit_prompt = default_prompt.replace("__tone__", selected_tone)

    with st.spinner("Generating batch requests..."):
        start_time = time.time()
        jsonl_path = zip_to_jsonl(uploaded_file
                                , None
                                , submit_prompt
                                , model="gpt-4o-mini"
                                , maxsize=customer_settings["max_size_tuple"]
                                )
        elapsed = time.time() - start_time
        print(f"zip_to_jsonl() took {elapsed:.2f} seconds.")

    with st.spinner("Uploadingn file for batch job..."):
        start_time = time.time()
        batch_input_f= upload_batch_file(client, jsonl_path)
        elapsed = time.time() - start_time
        st.write(f'Uploaded file ID: {batch_input_f.id}')
        print(f"upload_batch_file() took {elapsed:.2f} seconds.")

    with st.spinner("Creating batch job..."):
        start_time = time.time()
        batch = create_batch(client,batch_input_f)
        elapsed = time.time() - start_time
        print(f"create_batch() took {elapsed:.2f} seconds.")


st.header("Submitted Batches")
batches = client.batches.list(limit=10)
print(f'\n{batches.data}\n')
st.table(pd.DataFrame(columns=['id','status','output_file_id','created_at']
                      , data=[(b.id, b.status, b.output_file_id, b.created_at) for b in batches.data]
                      )
            )

test_file = 'file-4EJVyAfs4XsghM2ZxWbxKp'

file_response = client.files.content(test_file)
lines = file_response.text.strip().split("\n")
records = [json.loads(line) for line in lines]

for r in records : 
    st.write(r['response']['body']['output'][0]["content"][0]["text"])

st.table(load_finished_captions(client, test_file))

