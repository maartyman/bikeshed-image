#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-spec.bs}"
OUTDIR="${2:-dist}"

SCRIPT="/usr/local/bin/plantuml.py"
if [ -f "/work/plantuml.py" ]; then
    SCRIPT="/work/plantuml.py"
fi

run_build() {
    rm -rf "$OUTDIR"
    mkdir -p "$OUTDIR"

    if [ -f "/work/logo.png" ]; then
        cp /work/logo.png "$OUTDIR"
    fi

    python3 "$SCRIPT" "$INPUT" "$OUTDIR"
    bikeshed spec "$OUTDIR/spec.bs" "$OUTDIR/index.html"
    if [ -n "${DEV_PORT:-}" ]; then
        DEV_PORT="$DEV_PORT" OUTDIR="$OUTDIR" python3 - <<'PY'
import os
import pathlib

outdir = pathlib.Path(os.environ["OUTDIR"])
port = os.environ["DEV_PORT"]
path = outdir / "index.html"

if not path.exists():
    raise SystemExit(0)

html = path.read_text(encoding="utf-8")
if "livereload.js" in html:
    raise SystemExit(0)

script = (
    '<script type="text/javascript">(function(){'
    'var s=document.createElement("script");'
    f'var port={port};'
    's.src="//"+window.location.hostname+":"+port+"/livereload.js?port="+port;'
    'document.head.appendChild(s);'
    '})();</script>'
)

if "</head>" in html:
    html = html.replace("</head>", script + "</head>", 1)
elif "<head>" in html:
    html = html.replace("<head>", "<head>" + script, 1)
else:
    html = script + html

path.write_text(html, encoding="utf-8")
PY
    fi
}

WATCH_PID=""
LIVERELOAD_PID=""

shutdown() {
    if [ -n "$WATCH_PID" ]; then
        kill "$WATCH_PID" 2>/dev/null || true
    fi
    if [ -n "$LIVERELOAD_PID" ]; then
        kill "$LIVERELOAD_PID" 2>/dev/null || true
    fi
    exit 0
}

trap shutdown INT TERM

if [ "${DEV:-0}" != "0" ]; then
    echo "Dev mode enabled (watch + live reload)."
    PORT="${PORT:-59754}"
    DEV_PORT="$PORT"
    run_build
    livereload -t /work/dist -p "$PORT" --host 0.0.0.0 /work/dist &
    LIVERELOAD_PID=$!
    while true; do
        inotifywait -r -e modify,create,delete,move \
            --exclude '(^|/)(dist|\\.git)/' \
            /work >/dev/null 2>&1 &
        WATCH_PID=$!
        wait "$WATCH_PID"
        WATCH_PID=""
        run_build
    done
else
    run_build
fi
