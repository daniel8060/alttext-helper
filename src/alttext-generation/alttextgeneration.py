import streamlit as st
import openai
from PIL import Image
import io
import base64

from config import get_client_settings

def encode_image(im : Image.Image) -> str:
    """Convert the uploaded image to a base64 encoded string."""
    #get the image bytes
    image_bytes = io.BytesIO()
    im.save(image_bytes, format="JPEG")
    image_bytes.seek(0)  # Move the cursor to the beginning of the BytesIO

    #ecnode the bytes to base64 and decode to utf-8
    return base64.b64encode(image_bytes.getvalue()).decode("utf-8")

def downsample_image(image : Image.Image, max_size: tuple[int]):
    """Downsample the image if it exceeds the max size."""
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image = image.resize(max_size, Image.Resampling.LANCZOS)
    return image

# Access the secret key
openai.api_key = st.secrets["openai"]["api_key"]

#get the client settings
client_settings = get_client_settings()
default_prompt = client_settings['prompt']

st.title("Alt-Text Generator")

st.write(client_settings["max_size_tuple"])

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

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    subm = st.form_submit_button("Generate Alt Text")

if subm and uploaded_file:

    raw_bytes = uploaded_file.read()  # Read the raw bytes of the uploaded file

    byte_stream = io.BytesIO(raw_bytes)  # Create a BytesIO stream from the raw bytes
    image = Image.open(byte_stream) #now turn it into an image

    # st.image(image, caption="Uploaded Image", use_container_width=True)

    #  Resize if larger than your threshold (optional safeguard)
    image = downsample_image(image, max_size=client_settings["max_size_tuple"])

    # Read the image as bytes
    image_bytes = encode_image(image)

    submit_prompt = default_prompt.replace("__tone__", selected_tone)

    with st.spinner("Generating alt text..."):
        response = openai.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": submit_prompt},
                        {"type": "input_image",
                            "image_url": "data:image/jpeg;base64," + image_bytes,
                        },
                    ],
                }
            ],
        )

        alt_text = response.output_text
        st.success(f"Generated Alt Text:\n{alt_text}")