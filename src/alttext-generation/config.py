from pathlib import Path
import yaml
from typing import Any

def get_client_settings() -> dict[str,str|int]:
    """Load the client settings from the config file."""
    config_path = Path(__file__).parent / "clientsettings.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    config["prompt"] = config["prompt_template"].format(
        max_length=config["max_length"]
    )
    config["max_size_tuple"] = tuple(config["max_image_size"].values())

    return config
