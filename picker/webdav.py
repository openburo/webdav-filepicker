from webdav4.client import Client

WEBDAV_URL = "http://localhost:8080"

client = Client(WEBDAV_URL)


def file_info(path: str) -> dict:
    """Get metadata for a single file."""
    info = client.info(path)
    return {
        "name": info.get("display_name") or path.rstrip("/").rsplit("/", 1)[-1],
        "path": path,
        "size": info.get("content_length"),
        "content_type": info.get("content_type", ""),
        "modified": str(info["modified"]) if info.get("modified") else "",
    }


def download_file(path: str) -> bytes:
    """Download a file and return its content."""
    import io

    buf = io.BytesIO()
    client.download_fileobj(path, buf)
    return buf.getvalue()


def upload_bytes(directory: str, filename: str, data: bytes) -> None:
    """Upload bytes to the given directory."""
    import io

    remote_path = directory.rstrip("/") + "/" + filename
    client.upload_fileobj(io.BytesIO(data), remote_path)


def download_from_url(url: str) -> bytes:
    """Download content from an external URL."""
    import httpx

    resp = httpx.get(url)
    resp.raise_for_status()
    return resp.content


def remove(path: str) -> None:
    """Delete a file or directory."""
    client.remove(path)


def mkdir(path: str) -> None:
    """Create a directory."""
    client.mkdir(path)


def list_files(path: str = "/") -> list[dict]:
    """List files and directories at the given path."""
    entries = client.ls(path, detail=True)
    results = []
    for entry in entries:
        href = entry["href"]
        # Skip the directory itself
        if href.rstrip("/") == path.rstrip("/"):
            continue
        is_dir = entry["type"] == "directory"
        results.append(
            {
                "name": entry.get("display_name")
                or href.rstrip("/").rsplit("/", 1)[-1],
                "path": href,
                "is_dir": is_dir,
                "size": entry.get("content_length") if not is_dir else None,
                "content_type": entry.get("content_type", ""),
                "modified": str(entry["modified"]) if entry.get("modified") else "",
            }
        )
    return results
