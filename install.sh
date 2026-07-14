#!/bin/sh
set -eu

case "$(uname -s)" in
  Darwin) destination="$HOME/Library/Application Support/Commander/plugins/archive-fs" ;;
  Linux) destination="${XDG_DATA_HOME:-$HOME/.local/share}/commander/plugins/archive-fs" ;;
  *) echo "On Windows, copy this folder to %APPDATA%\\Commander\\plugins\\archive-fs" >&2; exit 1 ;;
esac

mkdir -p "$destination"
cp "$(dirname "$0")/plugin.json" "$(dirname "$0")/archivefs.py" "$destination/"
echo "Installed archive-fs in $destination"
