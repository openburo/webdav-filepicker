import json
from pathlib import Path

from quart import Quart, render_template

app = Quart(__name__)

CAPABILITIES_PATH = Path(__file__).parent.parent / "capabilities.json"


def load_picker_url() -> str:
    data = json.loads(CAPABILITIES_PATH.read_text())
    for cap in data["capabilities"]:
        if cap["action"] == "PICK":
            return cap["path"]
    raise ValueError("No PICK capability found")


@app.route("/")
async def index():
    picker_url = load_picker_url()
    return await render_template("index.html", picker_url=picker_url)
