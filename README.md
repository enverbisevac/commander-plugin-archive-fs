# Archive Filesystem for Commander

A small, cross-platform [Commander](https://enver.bisevac.com/commander) protocol-v1
plugin that lets you browse a tar or zip archive as a read-only filesystem — navigate
its directories and preview files in place, without extracting the whole thing first.

It handles `.tar`, `.tgz`, `.tbz2`, `.txz`, `.zip`, `.cbz`, and `.jar` using Python's
built-in `tarfile` and `zipfile` modules — no third-party packages, so it runs the same
on macOS, Linux, and Windows.

## Install

Python 3.9 or newer is recommended.

```sh
./install.sh
```

Restart Commander. Select a supported archive and choose **Browse as folder** from the
entry menu; the pane opens the archive under the `archivefs://` scheme. It is read-only:
files can be previewed and copied out, but the archive is never modified.

To install manually, copy this directory to Commander's user plugin folder:

- macOS: `~/Library/Application Support/Commander/plugins/archive-fs`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/commander/plugins/archive-fs`
- Windows: `%APPDATA%\Commander\plugins\archive-fs`

## Test and develop

Run the fs methods directly:

```sh
python3 archivefs.py fs.list '{"uri":"archivefs:///<percent-encoded-archive-path>/"}'
python3 archivefs.py fs.read '{"uri":"archivefs:///<percent-encoded-archive-path>/inner/file.txt"}'
```

The program writes exactly one JSON reply to stdout. Diagnostics belong on stderr.
A handled problem returns exit status 0 with `{"ok":false,"error":"..."}`, allowing
Commander to fall back safely.

## Protocol

Commander drives a plugin as a one-shot subprocess: `<exec...> <method> <paramsJson>`,
reading one JSON object from stdout. This plugin implements the read-only `fs` capability
(`fs.list`, `fs.read`) for the `archivefs` scheme. The full wire protocol and catalog
schema live in the [Commander documentation](https://enver.bisevac.com/commander).

## Packaging

A marketplace entry points at a zip of `plugin.json` + the executable at its root, plus
the archive's SHA-256 checksum. The [commander-plugins](https://github.com/enverbisevac/commander-plugins)
catalog builds that automatically from the pinned submodule.

## License

MIT.
