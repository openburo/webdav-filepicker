from base64 import b64encode
from fnmatch import fnmatch

from quart import Quart, flash, jsonify, render_template, request, redirect, url_for

from picker.webdav import download_file, list_files, mkdir, remove

app = Quart(__name__)
app.secret_key = "dev"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path


def build_breadcrumb(path: str) -> list[dict]:
    parts = path.strip("/").split("/") if path.strip("/") else []
    crumbs = [{"name": "🏠", "path": "/"}]
    accumulated = "/"
    for part in parts:
        accumulated += part + "/"
        crumbs.append({"name": part, "path": accumulated})
    return crumbs


def matches_mime_filter(content_type: str, allowed: list[str]) -> bool:
    """Check if a content type matches any of the allowed MIME patterns."""
    if not allowed or "*/*" in allowed:
        return True
    for pattern in allowed:
        if fnmatch(content_type, pattern):
            return True
    return False


def parse_intent_params() -> dict:
    """Parse intent parameters from query string."""
    return {
        "client_url": request.args.get("clientUrl", ""),
        "intent_id": request.args.get("id", ""),
        "multiple": request.args.get("multiple", "false") == "true",
        "allowed_mime_types": request.args.get("allowedMimeTypes", "").split(",")
        if request.args.get("allowedMimeTypes")
        else [],
        "type": request.args.get("type", "url").split(","),
    }


@app.route("/delete/<path:path>", methods=["POST"])
async def delete(path: str):
    if not path.startswith("/"):
        path = "/" + path
    name = path.rstrip("/").rsplit("/", 1)[-1]
    parent = path.rstrip("/").rsplit("/", 1)[0] or "/"
    remove(path)
    await flash(f"{name} supprimé")
    return redirect(url_for("browse", path=parent.lstrip("/")))


@app.route("/mkdir/")
@app.route("/mkdir/<path:path>")
async def new_dir(path: str = "/"):
    path = normalize_path(path)
    return await render_template("mkdir.html", current_path=path)


@app.route("/mkdir/", methods=["POST"])
@app.route("/mkdir/<path:path>", methods=["POST"])
async def create_dir(path: str = "/"):
    path = normalize_path(path)
    form = await request.form
    name = form.get("dirname", "").strip()
    if name:
        mkdir(path.rstrip("/") + "/" + name)
    return redirect(url_for("browse", path=path.lstrip("/"), **request.args))


@app.route("/api/content/<path:path>")
async def content(path: str):
    if not path.startswith("/"):
        path = "/" + path
    data = download_file(path)
    return jsonify({"content": b64encode(data).decode()})


@app.route("/")
@app.route("/browse/")
@app.route("/browse/<path:path>")
async def browse(path: str = "/"):
    path = normalize_path(path)
    intent = parse_intent_params()
    entries = list_files(path)

    dirs = sorted([e for e in entries if e["is_dir"]], key=lambda e: e["name"])
    files = sorted([e for e in entries if not e["is_dir"]], key=lambda e: e["name"])

    if intent["allowed_mime_types"]:
        files = [
            f
            for f in files
            if matches_mime_filter(f["content_type"], intent["allowed_mime_types"])
        ]

    return await render_template(
        "index.html",
        entries=[*dirs, *files],
        breadcrumb=build_breadcrumb(path),
        current_path=path,
        intent=intent,
    )
