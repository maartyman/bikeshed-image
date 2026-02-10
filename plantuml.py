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

    plantuml_pattern = re.compile(r'<pre class="plantuml">\s*(.*?)\s*</pre>', re.DOTALL)
    uml_dir = outdir / "uml"
    uml_dir.mkdir(parents=True, exist_ok=True)
    required_svgs: set[str] = set()

    def format_code(block: str, max_lines: int = 200) -> str:
        lines = block.splitlines()
        rendered: list[str] = []
        for index, line in enumerate(lines[:max_lines], start=1):
            rendered.append(f"{index:>4}: {line}")
        if len(lines) > max_lines:
            rendered.append("... (truncated)")
        return "\n".join(rendered)

    def plantuml_replacement(match: re.Match[str]) -> str:
        code = match.group(1).strip()
        if "@startuml" not in code or "@enduml" not in code:
            # Leave non-PlantUML blocks untouched.
            return match.group(0)
        # Use a short, deterministic hash for the filename to
        # avoid hitting filesystem path length limits.
        digest = hashlib.sha1(code.encode("utf-8")).hexdigest()
        filename = f"{digest}.svg"
        required_svgs.add(filename)
        local_path = uml_dir / filename

        # Generate and cache the SVG locally if it doesn't exist yet.
        if not local_path.exists():
            result = subprocess.run(
                ["plantuml", "-tsvg", "-pipe", "-charset", "UTF-8"],
                input=code.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace").strip()
                stdout = result.stdout.decode("utf-8", errors="replace").strip()
                details = "\n".join(part for part in [stderr, stdout] if part)
                message = "PlantUML failed"
                if details:
                    message = f"{message}:\n{details}"
                message = f"{message}\n\nDiagram:\n{format_code(code)}"
                raise SystemExit(message)
            local_path.write_bytes(result.stdout)

        # Always reference the locally cached SVG from the spec.
        return f'<img src="uml/{filename}" alt="PlantUML Diagram" no-autosize>'

    expanded = plantuml_pattern.sub(plantuml_replacement, expanded)
    (outdir / "spec.bs").write_text(expanded, encoding="utf-8")

    # Clean up stale PlantUML artifacts from previous builds.
    hashed_svg = re.compile(r"^[0-9a-f]{40}\.svg$")
    for path in uml_dir.iterdir():
        if not path.is_file():
            continue
        if not hashed_svg.match(path.name):
            continue
        if path.name not in required_svgs:
            path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
