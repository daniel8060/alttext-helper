import streamlit as st
from PIL import Image
from openai import OpenAI
import io
import base64
import json
import time
import pandas as pd

from config import get_customer_settings
from utils import split_zip_to_batches_by_size, write_jsonl_batch, generate_batch_filename
from batch import upload_batch_file, create_batch, load_finished_captions

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

customer_settings = get_customer_settings()
default_prompt = customer_settings['prompt']

st.title("Alt-Text Batch Generator")
st.write(f"Max image size: {customer_settings['max_size_tuple']}")

# Input form
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
    uploaded_file = st.file_uploader("Upload a ZIP of images", type=["zip"])
    subm = st.form_submit_button("Generate Alt Text Batches")

if subm and uploaded_file:
    submit_prompt = default_prompt.replace("__tone__", selected_tone)
    all_batches = []
    with st.spinner("Splitting ZIP into batches..."):
        batches_generator = split_zip_to_batches_by_size(
            zip_path=uploaded_file,
            prompt=submit_prompt,
            maxsize=customer_settings["max_size_tuple"],
            model="gpt-4o-mini",
            max_lines=1000,
            max_bytes=190 * 1024 * 1024
        )
        for i, lines in enumerate(batches_generator):
            jsonl_path = generate_batch_filename(suffix=f"_part{i}")
            write_jsonl_batch(lines, jsonl_path)
            st.success(f"Wrote batch file: {jsonl_path.name}")

            with st.spinner("Uploading batch file..."):
                batch_input_f = upload_batch_file(client, jsonl_path)
                st.write(f"Uploaded file ID: {batch_input_f.id}")

            with st.spinner("Creating batch job..."):
                batch = create_batch(client, batch_input_f)
                all_batches.append(batch)
                st.write(f"Created batch: {batch.id}")

    st.success("All batches created successfully.")

# List recent batches
st.header("Recent Batches")
batches = client.batches.list(limit=10)
st.table(pd.DataFrame(
    columns=["id", "status", "output_file_id", "created_at"],
    data=[(b.id, b.status, b.output_file_id, b.created_at) for b in batches.data]
))

# Optionally test a known output file
test_file = st.text_input("Output File ID to Preview Captions", value="")
if test_file:
    file_response = client.files.content(test_file)
    lines = file_response.text.strip().split("\n")
    records = [json.loads(line) for line in lines]

    st.subheader("Sample Captions")
    for r in records:
        st.write(r["response"]["body"]["output"][0]["content"][0]["text"])

    st.table(load_finished_captions(client, test_file))
