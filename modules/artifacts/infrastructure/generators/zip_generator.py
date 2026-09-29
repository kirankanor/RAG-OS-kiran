from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping
from pathlib import PurePosixPath


def build_zip(files: Mapping[str, str | bytes]) -> bytes:
    """In-memory, deterministic zip (sorted entries, fixed timestamps). Names are
    forward-slash relative paths; absolute paths and '..' are rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            p = PurePosixPath(name)
            if not name or p.is_absolute() or ".." in p.parts or "\\" in name:
                raise ValueError(f"Unsafe zip entry name: {name!r}")
            content = files[name]
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content.encode("utf-8") if isinstance(content, str) else content)
    return buf.getvalue()
