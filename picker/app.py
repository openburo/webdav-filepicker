from base64 import b64decode, b64encode
from fnmatch import fnmatch

from quart import (
    Quart,
    Response,
    flash,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
)

from picker.webdav import (
    download_file,
    download_from_url,
    file_info,
    list_files,
    mkdir,
    remove,
    upload_bytes,
)

import os

app = Quart(__name__)
app.secret_key = "dev"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")


def public_base_url() -> str:
    if PUBLIC_URL:
        return PUBLIC_URL.rstrip("/")
    return request.host_url.rstrip("/")


def normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path


def build_breadcrumb(path: str) -> list[dict]:
    parts = path.strip("/").split("/") if path.strip("/") else []
    crumbs = [{"name": "home", "path": "/", "is_home": True}]
    accumulated = "/"
    for part in parts:
        accumulated += part + "/"
        crumbs.append({"name": part, "path": accumulated, "is_home": False})
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
        "action": request.args.get("action", "PICK"),
        "client_url": request.args.get("clientUrl", ""),
        "intent_id": request.args.get("id", ""),
        "multiple": request.args.get("multiple", "false") == "true",
        "allowed_mime_types": request.args.get("allowedMimeTypes", "").split(",")
        if request.args.get("allowedMimeTypes")
        else [],
        "type": request.args.get("type", "sharingUrl").split(","),
        "save_name": request.args.get("name", ""),
        "save_mime_type": request.args.get("mimeType", ""),
        "save_size": request.args.get("size", ""),
        "source_type": request.args.get("sourceType", "payload"),
        "download_url": request.args.get("downloadUrl", ""),
    }


@app.route("/.well-known/openburo-capabilities.json")
async def capabilities():
    return jsonify(
        {
            "id": "webdav-filepicker",
            "name": "WebDAV File Picker",
            "version": "1",
            "url": public_base_url(),
            "capabilities": [
                {
                    "action": "PICK",
                    "properties": {"mimeTypes": ["*/*"]},
                    "path": public_base_url() + url_for("browse"),
                },
                {
                    "action": "SAVE",
                    "properties": {"mimeTypes": ["*/*"]},
                    "path": public_base_url() + url_for("browse"),
                },
            ],
        }
    )


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


@app.route("/preview/<path:path>")
async def preview(path: str):
    if not path.startswith("/"):
        path = "/" + path
    info = file_info(path)
    is_image = info["content_type"].startswith("image/")
    parent = path.rsplit("/", 1)[0] or "/"
    return await render_template(
        "preview.html",
        file=info,
        is_image=is_image,
        raw_url=url_for("raw", path=path.lstrip("/")),
        parent_url=url_for("browse", path=parent.lstrip("/")),
    )


@app.route("/raw/<path:path>")
async def raw(path: str):
    if not path.startswith("/"):
        path = "/" + path
    info = file_info(path)
    data = download_file(path)
    return Response(data, content_type=info["content_type"])


@app.route("/api/content/<path:path>")
async def content(path: str):
    if not path.startswith("/"):
        path = "/" + path
    data = download_file(path)
    return jsonify({"content": b64encode(data).decode()})


@app.route("/api/save/<path:path>", methods=["POST"])
async def api_save(path: str):
    """Save a file to the given directory. Accepts JSON with payload (base64) or downloadUrl."""
    if not path.startswith("/"):
        path = "/" + path
    body = await request.get_json()
    name = body["name"]
    if "payload" in body:
        data = b64decode(body["payload"])
    elif "downloadUrl" in body:
        data = download_from_url(body["downloadUrl"])
    else:
        return jsonify({"error": "No payload or downloadUrl provided"}), 400
    upload_bytes(path, name, data)
    file_path = path.rstrip("/") + "/" + name
    return jsonify(
        {
            "name": name,
            "sharingUrl": public_base_url()
            + url_for("preview", path=file_path.lstrip("/")),
            "downloadUrl": f"http://localhost:8080{file_path}",
        }
    )


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
