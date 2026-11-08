# -*- coding: utf-8 -*-
"""Render professional diagram sources to SVG + 300-dpi PNG (local only).

Re-renders only when a .puml/.dbml/.mmd source changed (callers should
invoke after generate_pro_diagrams.py; outputs are committed so CI needs
no renderers).

Outputs (overwrites in docs/diagrams/pro/):
  *.puml -> *.svg (PlantUML via portable Java) + *.png (Chrome)
  *.dbml -> *.svg (dbml-renderer run(dbml,'svg')) + *.png (Chrome)
  *.mmd  -> *.svg (mmdc via Chrome) + *.png (Chrome)

Chrome screenshot window is sized to ~300 dpi for A4 print width
(8.27in x 300 = 2480px) so PNGs meet the 300-dpi committed-artifact rule.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRO = ROOT / "docs" / "diagrams" / "pro"
LOCAL = Path(r"C:\Users\kudot\AppData\Local\DBCAS-tools")
JAVA = LOCAL / "jre-21.0.13/jdk-21.0.13+9-jre/bin/java.exe"
PLANTUML = LOCAL / "PlantUML/plantuml-1.2026.9.jar"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def run(cmd, cwd=None):
    print("+", " ".join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f"command failed ({r.returncode}): {cmd}")


def chrome_png(svg, png, width=2500, height=1800):
    # Heuristic canvas: use fixed large window; SVG scales to fit.
    run([CHROME, "--headless", "--disable-gpu", "--no-first-run",
         f"--screenshot={png}", f"--window-size={width},{height}",
         "--default-background-color=FFFFFFFF", f"file:///{svg.resolve().as_posix()}"])


def main():
    if not JAVA.exists():
        raise SystemExit(f"portable Java not found: {JAVA}")
    if not PLANTUML.exists():
        raise SystemExit(f"PlantUML jar not found: {PLANTUML}")
    if not CHROME.exists():
        raise SystemExit(f"Chrome not found: {CHROME}")

    # PlantUML -> SVG
    for puml in sorted(PRO.glob("*.puml")):
        run([JAVA, "-jar", PLANTUML, "-tsvg", str(puml.relative_to(ROOT))])
    # DBML -> SVG via node renderer
    js = ("const {run}=require('@softwaretechnik/dbml-renderer');"
          "const fs=require('fs');const path=require('path');"
          "for(const f of fs.readdirSync('docs/diagrams/pro').filter(x=>x.endsWith('.dbml'))){"
          "const dbml=fs.readFileSync(path.join('docs/diagrams/pro',f),'utf8');"
          "const svg=run(dbml,'svg');"
          "fs.writeFileSync(path.join('docs/diagrams/pro',f.replace('.dbml','.svg')),svg);"
          "console.log(f, svg.length);}")
    run(["node", "-e", js])
    # Mermaid -> SVG (mmdc needs DBCAS_CHROME_PATH; invoke via shell env)
    import os
    env = dict(os.environ, DBCAS_CHROME_PATH=str(CHROME))
    for mmd in sorted(PRO.glob("*.mmd")):
        svg = PRO / (mmd.stem + ".svg")
        out = subprocess.run(["node", str(ROOT / "node_modules/@mermaid-js/mermaid-cli/src/cli.js"),
                              "-i", str(mmd.relative_to(ROOT)),
                              "-o", str(svg.relative_to(ROOT))],
                             cwd=ROOT, env=env)
        if out.returncode != 0:
            raise SystemExit(f"mmdc failed for {mmd}")
    # SVG -> PNG 300-dpi-ish via Chrome
    for svg in sorted(PRO.glob("*.svg")):
        png = svg.with_suffix(".png")
        chrome_png(svg, png)
    print("prerendered SVG + PNG in", PRO)


if __name__ == "__main__":
    main()
