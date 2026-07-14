#!/usr/bin/env python3
"""Commander filesystem plugin: browse tar/zip archives (protocol v1).

Presents a tar or zip archive as a read-only *filesystem* — you navigate into
its directories and preview files without ever extracting it (distinct from the
packer plugins, which unpack). Pure Python standard library (`tarfile`/
`zipfile`), so it works anywhere.

URI form:  archivefs://<url-encoded-container-path>/<inner-path>
  e.g.     archivefs://%2Ftmp%2Fbundle.tar/docs   -> the "docs" dir inside
                                                      /tmp/bundle.tar

Methods:
  fs.list {uri}            -> {ok, entries:[{name,is_dir,size,mtime}]}
  fs.read {uri, maxBytes}  -> {ok, data_base64}
"""
import base64
import json
import os
import sys
import tarfile
import urllib.parse
import zipfile

SCHEME = "archivefs://"


def out(obj):
    print(json.dumps(obj))
    sys.exit(0)


def fail(msg):
    out({"ok": False, "error": str(msg)})


def parse_uri(uri):
    if not uri.startswith(SCHEME):
        fail("not an archivefs uri")
    rest = uri[len(SCHEME):]
    slash = rest.find("/")
    if slash < 0:
        host, inner = rest, ""
    else:
        host, inner = rest[:slash], rest[slash + 1:]
    container = urllib.parse.unquote(host)
    return container, inner.strip("/")


def children(all_names, inner):
    """Immediate children of `inner` given a flat list of (name, is_dir, size,
    mtime) archive members. Synthesizes directories that exist only implicitly
    (a member `a/b/c.txt` implies dirs `a` and `a/b`)."""
    prefix = inner + "/" if inner else ""
    seen = {}
    for name, is_dir, size, mtime in all_names:
        n = name.rstrip("/")
        if not n or not n.startswith(prefix):
            continue
        rest = n[len(prefix):]
        if not rest:
            continue
        first = rest.split("/", 1)[0]
        deeper = "/" in rest
        if first not in seen:
            seen[first] = {
                "name": first,
                "is_dir": True if deeper else is_dir,
                "size": 0 if deeper or is_dir else size,
                "mtime": 0 if deeper else mtime,
            }
        elif not deeper and not is_dir:
            # A file shadowing a previously-synthesized dir shouldn't happen,
            # but prefer real file metadata if we somehow see it.
            seen[first].update({"size": size, "mtime": mtime})
    return sorted(seen.values(), key=lambda e: (not e["is_dir"], e["name"].lower()))


def norm(name):
    """Normalize an archive member name: drop a leading `./` (tars made with
    `-C dir .` prefix everything) and any leading slashes."""
    n = name.strip()
    while n.startswith("./"):
        n = n[2:]
    return n.lstrip("/")


def members_tar(tf):
    for m in tf.getmembers():
        if m.isdir() or m.isfile():
            n = norm(m.name)
            if n and n != ".":
                yield (n, m.isdir(), m.size, int(m.mtime))


def members_zip(zf):
    for info in zf.infolist():
        n = norm(info.filename)
        if n and n != ".":
            yield (n, info.is_dir(), info.file_size, 0)


def do_list(uri):
    container, inner = parse_uri(uri)
    if not os.path.exists(container):
        fail("container not found")
    try:
        if zipfile.is_zipfile(container):
            with zipfile.ZipFile(container) as zf:
                entries = children(list(members_zip(zf)), inner)
        elif tarfile.is_tarfile(container):
            with tarfile.open(container) as tf:
                entries = children(list(members_tar(tf)), inner)
        else:
            fail("unsupported container (not tar or zip)")
    except (tarfile.TarError, zipfile.BadZipFile, OSError) as e:
        fail("cannot read container: %s" % e)
    out({"ok": True, "entries": entries})


def do_read(uri, max_bytes):
    container, inner = parse_uri(uri)
    if not inner:
        fail("no file path")
    if not os.path.exists(container):
        fail("container not found")
    try:
        if zipfile.is_zipfile(container):
            with zipfile.ZipFile(container) as zf:
                real = next((n for n in zf.namelist() if norm(n) == inner), None)
                if real is None:
                    fail("file not found in archive")
                with zf.open(real) as f:
                    data = f.read(max_bytes)
        elif tarfile.is_tarfile(container):
            with tarfile.open(container) as tf:
                m = next((x for x in tf.getmembers() if norm(x.name) == inner and x.isfile()), None)
                if m is None:
                    fail("file not found in archive")
                f = tf.extractfile(m)
                data = f.read(max_bytes) if f else b""
        else:
            fail("unsupported container")
    except (tarfile.TarError, zipfile.BadZipFile, OSError) as e:
        fail("cannot read file: %s" % e)
    out({"ok": True, "data_base64": base64.b64encode(data).decode("ascii")})


def main():
    if len(sys.argv) < 3:
        fail("usage: archivefs.py <method> <paramsJson>")
    method = sys.argv[1]
    try:
        params = json.loads(sys.argv[2])
    except (ValueError, IndexError):
        fail("bad params json")
    uri = params.get("uri")
    if not uri:
        fail("no uri")
    if method == "fs.list":
        do_list(uri)
    elif method == "fs.read":
        do_read(uri, int(params.get("maxBytes", 8 * 1024 * 1024)))
    else:
        fail("unknown method: %s" % method)


if __name__ == "__main__":
    main()
