from PIL import Image
import zipfile
import json 
import io 
import base64
import datetime
import uuid
from pathlib import Path
from openai import OpenAI


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


def zip_to_jsonl(zip_path: str, jsonl_path: str = None, prompt: str = None, maxsize: tuple[int] = None, model: str = "gpt-4o-mini"):
    
    if jsonl_path is None:
        jsonl_path = generate_batch_filename()
    jsonl_path = Path(jsonl_path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)


    with zipfile.ZipFile(zip_path, 'r') as archive:
        entries = []
        for file in archive.namelist():
            # Skip macOS metadata files
            if file.startswith("__MACOSX/") or file.split("/")[-1].startswith("._"):
                continue
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            try:
                with archive.open(file) as f:
                    image = Image.open(f).convert("RGB")
                    image = downsample_image(image, max_size=maxsize)
                    encoded_image = encode_image(image)
                    entry = {
                        "custom_id": file,
                        "method": "POST",
                        "url": "/v1/responses",
                        "body": {
                            "model": model,
                            "input": [
                                            {
                                                "role": "user",
                                                "content": [
                                                    {"type": "input_text", "text": prompt},
                                                    {"type": "input_image",
                                                        "image_url": "data:image/jpeg;base64," + encoded_image,
                                                    },
                                                ],
                                            }
                                ],
                        }
                    }
                    entries.append(entry)
            except Exception as e:
                print(f"Skipping {file}: {e}")

    # Save to JSONL
    with open(jsonl_path, "w") as out:
        for item in entries:
            out.write(json.dumps(item) + "\n")

    print(f"✅ Exported {len(entries)} entries to {jsonl_path}")

    return jsonl_path


def zip_to_jsonl_stream(zip_file: io.BytesIO, prompt: str, maxsize : tuple[int], model: str = "gpt-4o-mini") -> io.StringIO:
    """Convert a zip file (as BytesIO) of images into a JSONL stream compatible with OpenAI's responses endpoint."""
    archive = zipfile.ZipFile(zip_file)
    output_stream = io.StringIO()
    for file in archive.namelist():
        if not file.lower().endswith((".png", ".jpg", ".jpeg")):
            print(f"Skipping {file}: Not an image file")
            continue

        # Skip macOS metadata files
        if file.startswith("__MACOSX/") or file.split("/")[-1].startswith("._"):
            continue
        try:
            with archive.open(file) as f:
                image = Image.open(f).convert("RGB")

                image = downsample_image(image, max_size=maxsize)

                encoded_image = encode_image(image)
                entry = {
                    "custom_id": file,
                    "method": "POST",
                    "url": "/v1/responses",
                    "body": {
                        "model": model,
                        "input": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": prompt},
                                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded_image}"}
                                ]
                            }
                        ]
                    }
                }
                output_stream.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Skipping {file}: {e}")
    output_stream.seek(0)
    return output_stream


def generate_batch_filename(base_dir="batches", suffix="") -> Path:
    """Generate a unique filename for a batch JSONL file."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{unique_id}{suffix}.jsonl"
    return Path(base_dir) / filename


