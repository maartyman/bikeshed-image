#!/usr/bin/env python3
import hashlib
import pathlib
import re
import subprocess
import sys


def main() -> int:
    input_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("spec.bs")
    outdir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("dist")

    template = input_path.read_text(encoding="utf-8")
    pattern = re.compile(r'<pre class="include"\s+path="([^"]+)"></pre>')

    def replacement(match: re.Match[str]) -> str:
        rel_path = match.group(1)
        text = pathlib.Path(rel_path).read_text(encoding="utf-8").strip()
        # Ensure surrounding blank lines to keep sections separated.
        return "\n" + text + "\n"

    expanded = pattern.sub(replacement, template)

    plantuml_pattern = re.compile(
        r'<pre class="plantuml">\s*(@startuml.*?@enduml)\s*</pre>', re.DOTALL
    )
    uml_dir = outdir / "uml"
    uml_dir.mkdir(parents=True, exist_ok=True)

    def plantuml_replacement(match: re.Match[str]) -> str:
        code = match.group(1)
        # Use a short, deterministic hash for the filename to
        # avoid hitting filesystem path length limits.
        digest = hashlib.sha1(code.encode("utf-8")).hexdigest()
        filename = f"{digest}.svg"
        local_path = uml_dir / filename

        # Generate and cache the SVG locally if it doesn't exist yet.
        if not local_path.exists():
            result = subprocess.run(
                ["plantuml", "-tsvg", "-pipe"],
                input=code.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            local_path.write_bytes(result.stdout)

        # Always reference the locally cached SVG from the spec.
        return f'<img src="uml/{filename}" alt="PlantUML Diagram" no-autosize>'

    expanded = plantuml_pattern.sub(plantuml_replacement, expanded)
    (outdir / "spec.bs").write_text(expanded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
