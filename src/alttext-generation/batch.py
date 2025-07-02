from typing import Any
import json
import pandas as pd

def upload_batch_file(client, jsonl_path:str): 
    """Uploads a JSONL file to OpenAI for batch processing."""
    batch_input_file = client.files.create(
            file=open(jsonl_path, "rb"),
            purpose="batch",
        )
    
    return batch_input_file

def create_batch(client, batch_input_file) -> dict[str, Any]: 
    batch_input_file_id = batch_input_file.id

    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/responses",
        completion_window="24h"  # How long OpenAI has to process
    )

    return batch

def load_finished_captions(client, file_id: str) -> pd.DataFrame:
    """Load finished captions from a batch file."""
    file_response_t = client.files.content(file_id).text

    rows = []

    #use a generator for memory concerns
    records = (json.loads(line) for line in file_response_t.strip().split("\n"))

    for r in records: 

        #initialize caption to a bad value with identifying information 
        caption = f"No caption generated for file {r['custom_id']} in output_file {file_id}"

        #successful response, fill in the caption 
        if r['response']['status_code'] == 200:
            # Extract the caption from the response
            caption = r['response']['body']['output'][0]["content"][0]["text"]
            
        # Append the record to the DataFrame
        rows.append({
            'OUTPUT_FILE_ID': file_id,
            'INPUT_FILENAME': r['custom_id'],
            'CAPTION': caption
        }) 

    df = pd.DataFrame(rows)

    return df 

