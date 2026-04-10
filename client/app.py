import httpx
from quart import Quart, render_template

app = Quart(__name__)

PICKER_BASE_URL = "http://10.4.0.32:5000"


async def load_capabilities() -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PICKER_BASE_URL}/.well-known/capabilities.json")
        return resp.json()


async def get_capability_url(action: str) -> str:
    data = await load_capabilities()
    for cap in data["capabilities"]:
        if cap["action"] == action:
            return cap["path"]
    raise ValueError(f"No {action} capability found")


@app.route("/")
async def index():
    return await render_template("index.html")


@app.route("/pick")
async def pick():
    picker_url = await get_capability_url("PICK")
    return await render_template("pick.html", picker_url=picker_url)


@app.route("/save")
async def save():
    picker_url = await get_capability_url("SAVE")
    return await render_template("save.html", picker_url=picker_url)
