from quart import Quart, render_template, request, redirect, url_for

from picker.webdav import list_files, mkdir, upload_file

app = Quart(__name__)


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


@app.route("/mkdir/<path:path>", methods=["POST"])
async def create_dir(path: str = "/"):
    path = normalize_path(path)
    form = await request.form
    name = form.get("dirname", "").strip()
    if name:
        mkdir(path.rstrip("/") + "/" + name)
    return redirect(url_for("browse", path=path.lstrip("/")))


@app.route("/upload/<path:path>", methods=["POST"])
async def upload(path: str = "/"):
    path = normalize_path(path)
    files = (await request.files).getlist("files")
    for f in files:
        if f.filename:
            upload_file(path, f.filename, f.stream)
    return redirect(url_for("browse", path=path.lstrip("/")))


@app.route("/")
@app.route("/browse/")
@app.route("/browse/<path:path>")
async def browse(path: str = "/"):
    path = normalize_path(path)
    entries = list_files(path)
    dirs = sorted([e for e in entries if e["is_dir"]], key=lambda e: e["name"])
    files = sorted([e for e in entries if not e["is_dir"]], key=lambda e: e["name"])
    return await render_template(
        "index.html",
        entries=[*dirs, *files],
        breadcrumb=build_breadcrumb(path),
        current_path=path,
    )
