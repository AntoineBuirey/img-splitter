#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
uv run pyinstaller --noconfirm --clean img_splitter.spec

echo "Executable created at: $(pwd)/dist/img-splitter"
