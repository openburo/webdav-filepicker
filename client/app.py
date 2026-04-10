import httpx
from quart import Quart, render_template

app = Quart(__name__)

PICKER_BASE_URL = "http://10.4.0.32:5000"


async def load_picker_url() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PICKER_BASE_URL}/.well-known/capabilities.json")
        data = resp.json()
    for cap in data["capabilities"]:
        if cap["action"] == "PICK":
            return cap["path"]
    raise ValueError("No PICK capability found")


@app.route("/")
async def index():
    picker_url = await load_picker_url()
    return await render_template("index.html", picker_url=picker_url)
