# -*- coding: utf-8 -*-
"""Generate the three Word-document diagrams from the real project facts.

    python scripts/generate_doc_diagrams.py

Inputs (all generated from the repository, never hand-drawn):
  docs/qa/schema-introspection.json      real PostgreSQL introspection
  docs/qa/project-facts.json             Compose / OpenAPI / frontend routes
  docs/diagrams/generated/system-context-model.json   nodes/flows with evidence
  docs/diagrams/physical-schema.svg      graphviz rendering of the real schema

Outputs (SVG, later rasterised to high-res PNG by render_svg_png.mjs):
  docs/diagrams/generated/system-context.svg
  docs/diagrams/generated/erd.svg
  docs/diagrams/generated/table-relationships.svg
  docs/diagrams/generated/manifest.json
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "docs" / "diagrams" / "generated"
INTRO = json.load(open(ROOT / "docs/qa/schema-introspection.json", encoding="utf-8"))
CTX = json.load(open(GEN / "system-context-model.json", encoding="utf-8"))
FACTS = json.load(open(ROOT / "docs/qa/project-facts.json", encoding="utf-8"))

LEGACY = {"assessment", "assessment_concept", "assessment_question", "assessment_blueprint"}


def esc(s):
    return html.escape(str(s), quote=True)


def svg_header(width, height, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">\n'
            f'<title>{esc(title)}</title><desc>{esc(desc)}</desc>\n'
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#34495e"/></marker>'
            '<marker id="arrow-light" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            'markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#9aa7b4"/></marker>'
            '</defs>\n'
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>\n'
            f'<text x="24" y="34" font-family="Arial" font-size="26" font-weight="bold" fill="#10254f">{esc(title)}</text>\n')


# ---------------------------------------------------------------- system context
CTX_POS = {
    "learner": (40, 90), "admin": (40, 250), "frontend": (360, 90),
    "app": (700, 250), "db": (1400, 90), "mailpit": (1400, 620),
    "init": (1050, 90), "executor_image": (1050, 250), "sandbox": (1400, 250),
    "prompt_builder": (700, 470), "llm": (1050, 470), "google": (1400, 440),
    "github": (1400, 530), "qa_ai": (360, 470), "meter": (360, 620),
}
NODE_W, NODE_H = 290, 66


def ctx_rect(node):
    x, y = CTX_POS[node["id"]]
    kind = node["kind"]
    fill = {"actor": "#d9f0e6", "service": "#dceaf7", "service-qa": "#fdf1d6",
            "external": "#f3e2ef", "component": "#e8e2f5"}.get(kind, "#eef2f5")
    stroke = "#2b6c64" if kind == "actor" else "#34495e"
    qa = " (QA)" if kind == "service-qa" else ""
    return (f'<g id="node_{node["id"]}">'
            f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="8" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2"/>'
            f'<text x="{x+12}" y="{y+26}" font-family="Arial" font-size="17" font-weight="bold" '
            f'fill="#10254f">{esc(node["label"])}{qa}</text>'
            f'<text x="{x+12}" y="{y+47}" font-family="Arial" font-size="12" fill="#40556b">{esc(node["sub"])}</text>'
            f'<title>{esc(node["evidence"])}</title></g>\n')


def build_context():
    W, H = 1740, 1180
    parts = [svg_header(W, H, "System Context Diagram — DBCAS (generated from Compose + code)",
                        f'{len(CTX["nodes"])} nodes, {len(CTX["flows"])} directed labelled flows; '
                        "arrow IDs are decoded in the flow legend below; every flow carries evidence")]
    parts.append('<text x="24" y="62" font-family="Arial" font-size="13" fill="#5c6c7c">'
                 'Actors = green · services = blue · QA-only = amber · external systems = purple/pink · '
                 'arrows show the direction of data/control flow (Fxx = legend row)</text>\n')
    import math
    # Nodes are painted first so flow ID badges are never hidden behind a box.
    for node in CTX["nodes"]:
        parts.append(ctx_rect(node))
    used_midpoints = []
    for i, flow in enumerate(CTX["flows"]):
        a, b = CTX_POS[flow["source"]], CTX_POS[flow["destination"]]
        x1, y1 = a[0] + NODE_W / 2, a[1] + NODE_H / 2
        x2, y2 = b[0] + NODE_W / 2, b[1] + NODE_H / 2
        dx, dy = x2 - x1, y2 - y1
        dist = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / dist, dy / dist
        trim = NODE_W / 2 + 6
        sx, sy = x1 + ux * trim, y1 + uy * trim
        ex, ey = x2 - ux * trim, y2 - uy * trim
        qa = flow["source"] in ("qa_ai", "meter") or flow["destination"] in ("qa_ai", "meter")
        colour = "#b07b1a" if qa else "#34495e"
        marker = "arrow-light" if qa else "arrow"
        def inside_node(px, py):
            return any(nx - 6 <= px <= nx + NODE_W + 6 and ny - 6 <= py <= ny + NODE_H + 6
                       for nx, ny in CTX_POS.values())
        # Pick a point on the arrow that is neither inside a node box nor on
        # top of another badge; prefer the middle, then earlier/later points.
        candidates = [0.5, 0.38, 0.62, 0.28, 0.72, 0.2, 0.8]
        chosen = None
        for t in candidates:
            mx, my = sx + (ex - sx) * t, sy + (ey - sy) * t
            if not inside_node(mx, my) and all(math.hypot(mx - px, my - py) > 26
                                               for px, py in used_midpoints):
                chosen = (mx, my)
                break
        if chosen is None:
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            for attempt in range(12):
                if not inside_node(mx, my) and all(math.hypot(mx - px, my - py) > 26
                                                   for px, py in used_midpoints):
                    break
                mx += 26
                my += 22
        else:
            mx, my = chosen
        used_midpoints.append((mx, my))
        parts.append(f'<g id="flow_{flow["id"]}">'
                     f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                     f'stroke="{colour}" stroke-width="1.8" marker-end="url(#{marker})"/>'
                     f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="12" fill="#ffffff" stroke="{colour}"/>'
                     f'<text x="{mx:.1f}" y="{my+4:.1f}" font-family="Arial" font-size="10" font-weight="bold" '
                     f'text-anchor="middle" fill="#26384a">{esc(flow["id"])}</text>'
                     f'<title>{esc(flow["source"] + " -> " + flow["destination"] + " | " + flow["label"] + " | " + flow["evidence"])}</title></g>\n')
    # Full legend: two columns, every flow id + direction + label, no overlap.
    ly = 730
    parts.append(f'<rect x="24" y="{ly}" width="{W-48}" height="30" fill="#10254f"/>'
                 f'<text x="34" y="{ly+20}" font-family="Arial" font-size="15" font-weight="bold" '
                 f'fill="#ffffff">Flow legend — directed data/control flows (all derived from code/config)</text>\n')
    rows_per_col = (len(CTX["flows"]) + 1) // 2
    for i, flow in enumerate(CTX["flows"]):
        cx = 34 + (i // rows_per_col) * ((W - 68) // 2)
        cy = ly + 30 + 20 + (i % rows_per_col) * 19
        txt = f'{flow["id"]} {flow["source"]} → {flow["destination"]}: {flow["label"]}'
        parts.append(f'<g id="legend_{flow["id"]}"><text x="{cx}" y="{cy}" font-family="Arial" '
                     f'font-size="10.5" fill="#26384a">{esc(txt[:108])}</text>'
                     f'<title>{esc(flow["evidence"])}</title></g>\n')
    parts.append('</svg>\n')
    (GEN / "system-context.svg").write_text("".join(parts), encoding="utf-8")


# ---------------------------------------------------------------- ERD
def cardinality(fk, tables_by_name):
    t = tables_by_name[fk["source"]]
    cols = {c["name"]: c for c in t["columns"]}
    nullable = any(cols[c]["nullable"] for c in fk["columns"] if c in cols)
    unique_sets = [set(c["columns"]) for c in t["constraints"] if c["type"] in ("p", "u")]
    one_to_one = any(set(fk["columns"]) <= s for s in unique_sets)
    return ("0..1" if nullable else "1", "0..1" if one_to_one else "0..N")


def write_svg(path, width, height, title, desc, body):
    (GEN / path).write_text(svg_header(width, height, title, desc) + body + "</svg>\n",
                            encoding="utf-8")


def build_erd():
    """Write both the full ERD SVG and page-aligned SVGs (no split entity boxes)."""
    tables = INTRO["tables"]
    tbn = {t["table"]: t for t in tables}
    COLS, BOX_W, GAP_X, GAP_Y = 2, 430, 30, 24
    left, top = 30, 92
    width = left + COLS * BOX_W + (COLS - 1) * GAP_X + 30
    pk_cache = {}
    for t in tables:
        for c in t["constraints"]:
            if c["type"] == "p":
                pk_cache[t["table"]] = set(c["columns"])
    fk_cols = {}
    for f in INTRO["foreign_keys"]:
        fk_cols.setdefault(f["source"], set()).update(f["columns"])

    def table_frag(t, x, y):
        n = t["table"]
        h = 40 + 20 * len(t["columns"]) + 10
        legacy = n in LEGACY
        head = "#f6d99a" if legacy else "#dceaf7"
        s = [f'<g id="table_{esc(n)}">'
             f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{h}" fill="#ffffff" stroke="#34495e" stroke-width="1.4"/>'
             f'<rect x="{x}" y="{y}" width="{BOX_W}" height="28" fill="{head}"/>'
             f'<text x="{x+8}" y="{y+19}" font-family="Arial" font-size="14" font-weight="bold" '
             f'fill="#10254f">{esc(n)}{" [legacy/retired]" if legacy else ""}</text>\n']
        for i, c in enumerate(t["columns"]):
            marks = []
            if c["name"] in pk_cache.get(n, set()):
                marks.append("PK")
            if c["name"] in fk_cols.get(n, set()):
                marks.append("FK")
            mark = (" " + ",".join(marks)) if marks else ""
            typ = c["type"] + (f'({c["max_length"]})' if c["max_length"] else "")
            line = f'{c["name"]}: {typ}{mark}{" NULL" if c["nullable"] else " NOT NULL"}'
            s.append(f'<text x="{x+8}" y="{y+48+i*20}" font-family="Consolas,monospace" '
                     f'font-size="15" fill="#26384a">{esc(line[:58])}</text>\n')
        s.append('</g>\n')
        return "".join(s), h

    def fk_frag(f, y, idx):
        parent, child = cardinality(f, tbn)
        on = f'{f["on_delete"]}/{f["on_update"]}'
        txt = (f'{f["constraint"]}: {f["source"]}({",".join(f["columns"])}) → '
               f'{f["destination"]}({",".join(f["reference_columns"])}) '
               f'[{parent}:{child}] ON DELETE/UPDATE {on}')
        return (f'<g id="fk_{esc(f["constraint"])}"><text x="40" y="{y}" '
                f'font-family="Consolas,monospace" font-size="14" fill="#26384a">{esc(txt)}</text>'
                f'<title>{esc(f["definition"])}</title></g>\n')

    header_note = ('<text x="30" y="64" font-family="Arial" font-size="13" fill="#5c6c7c">'
                   'PK = primary key · FK = foreign key · NULL = nullable · '
                   'legacy/retired tables are shaded amber.</text>\n')
    # group tables into rows of two, then rows into pages with a height budget
    rows = []
    for i in range(0, len(tables), COLS):
        group = tables[i:i + COLS]
        heights = [40 + 20 * len(t["columns"]) + 10 for t in group]
        rows.append((group, max(heights)))
    BUDGET = 1050
    pages, cur, cur_h = [], [], 0
    for row in rows:
        if cur and cur_h + row[1] + GAP_Y > BUDGET:
            pages.append((cur, cur_h)); cur, cur_h = [], 0
        cur.append(row); cur_h += row[1] + GAP_Y
    if cur:
        pages.append((cur, cur_h))
    # FK panel pages (30 rows each) so no FK line is cut
    fk_pages = [INTRO["foreign_keys"][i:i + 30]
                for i in range(0, len(INTRO["foreign_keys"]), 30)]

    full_body = [header_note]
    full_y = top
    page_number = 0
    for page_rows, _ in pages:
        page_number += 1
        body = [header_note]
        y = top
        for group, rh in page_rows:
            for ci, t in enumerate(group):
                frag, _ = table_frag(t, left + ci * (BOX_W + GAP_X), y)
                body.append(frag)
                full_body.append(table_frag(t, left + ci * (BOX_W + GAP_X), full_y)[0])
            y += rh + GAP_Y
            full_y += rh + GAP_Y
        write_svg(f"erd-{page_number}.svg", width, int(y + 30),
                  f"Entity Relationship Diagram — DBCAS ({page_number}/{len(pages) + len(fk_pages)})",
                  f"41 bảng thật, thuộc tính PK/FK/kiểu/null; legacy/retired = {', '.join(sorted(LEGACY))}",
                  "".join(body))
    for fi, group in enumerate(fk_pages, 1):
        page_number += 1
        body = [header_note,
                f'<g id="relationship-panel"><rect x="30" y="{top}" width="{width-60}" height="28" fill="#10254f"/>'
                f'<text x="40" y="{top+19}" font-family="Arial" font-size="14" font-weight="bold" '
                f'fill="#ffffff">Foreign keys ({len(INTRO["foreign_keys"])}) — source → destination, '
                f'cardinality, ON DELETE/UPDATE</text></g>\n']
        y = top + 40
        for j, f in enumerate(group):
            body.append(fk_frag(f, y, j)); full_body.append(fk_frag(f, full_y, j))
            y += 19; full_y += 19
        write_svg(f"erd-{page_number}.svg", width, int(y + 30),
                  f"Entity Relationship Diagram — DBCAS ({page_number}/{len(pages) + len(fk_pages)})",
                  "Bảng quan hệ: mọi khóa ngoại với hướng, cột và cardinality", "".join(body))
    write_svg("erd.svg", width, int(full_y + 40),
              "Entity Relationship Diagram — DBCAS (real schema)",
              f'{len(tables)} tables, {sum(len(t["columns"]) for t in tables)} columns, '
              f'{len(INTRO["foreign_keys"])} foreign keys, {len(INTRO["indexes"])} indexes; '
              f'legacy tables: {", ".join(sorted(LEGACY))}', "".join(full_body))
    return len(tables), width, int(full_y + 40), page_number


# ---------------------------------------------------------------- table relationships
def build_table_relationships():
    """Directed FK diagram from introspection; full SVG + page-aligned SVGs."""
    tbn = {t["table"]: t for t in INTRO["tables"]}
    width, top = 950, 92
    header_h, row_h, chip_step = 40, 44, 20
    note = ('<text x="30" y="64" font-family="Arial" font-size="14" fill="#5c6c7c">'
            'Mỗi mũi tên đi từ bảng con (chứa FK) tới bảng cha (khóa được tham chiếu).</text>\n')

    def fk_frag(f, yy):
        parent, child = cardinality(f, tbn)
        line1 = (f'{f["constraint"]}: {f["source"]}({",".join(f["columns"])}) → '
                 f'{f["destination"]}({",".join(f["reference_columns"])})')
        line2 = (f'cardinality [{parent}:{child}] · ON DELETE {f["on_delete"]} · '
                 f'ON UPDATE {f["on_update"]}')
        if len(line1) > 104:
            cut = line1.rfind(" → ", 0, 110)
            if cut < 50:
                cut = line1.rfind(" ", 0, 104)
            l1a, l1b = line1[:cut], line1[cut:].strip()
        else:
            l1a, l1b = line1, None
        text = (f'<text x="58" y="{yy+14}" font-family="Consolas,monospace" font-size="12.5" '
                f'fill="#26384a">{esc(l1a)}</text>')
        if l1b:
            text += (f'<text x="58" y="{yy+28}" font-family="Consolas,monospace" font-size="12.5" '
                     f'fill="#26384a">{esc(l1b)}</text>')
        text += (f'<text x="58" y="{yy+(42 if l1b else 30)}" font-family="Consolas,monospace" '
                 f'font-size="11.5" fill="#5c6c7c">{esc(line2)}</text>')
        return (f'<g id="fk_{esc(f["constraint"])}">'
                f'<circle cx="46" cy="{yy+13}" r="4" fill="#217a79"/>'
                f'<path d="M{width-52} {yy+9} L{width-42} {yy+13} L{width-52} {yy+17} z" fill="#217a79"/>'
                + text + f'<title>{esc(f["definition"])}</title></g>\n')

    def chip_frag(t, x, y):
        legacy = t["table"] in LEGACY
        fill = "#f6d99a" if legacy else "#dceaf7"
        return (f'<g id="table_{esc(t["table"])}"><rect x="{x}" y="{y}" width="{(width-60)//2-10}" '
                f'height="17" fill="{fill}" stroke="#34495e" stroke-width="0.6"/>'
                f'<text x="{x+6}" y="{y+13}" font-family="Arial" font-size="12" fill="#10254f">'
                f'{esc(t["table"])}{" [legacy]" if legacy else ""}</text></g>\n')

    def header(y, label):
        return (f'<rect x="30" y="{y}" width="{width-60}" height="{header_h}" fill="#10254f"/>'
                f'<text x="40" y="{y+26}" font-family="Arial" font-size="16" font-weight="bold" '
                f'fill="#ffffff">{esc(label)}</text>\n')

    fks = INTRO["foreign_keys"]
    tables = INTRO["tables"]
    PER_PAGE = 20
    pages = [fks[i:i + PER_PAGE] for i in range(0, len(fks), PER_PAGE)]
    chips_per_page = (len(tables) + len(pages) - 1) // len(pages)
    full = [note, header(top, f'Khóa ngoại ({len(fks)} cạnh, hướng con → cha)')]
    fy = top + header_h + 24
    for f in fks:
        full.append(fk_frag(f, fy)); fy += row_h
    cy = fy + 20
    full.append(header(cy, f'Tất cả {len(tables)} bảng (legacy/retired tô màu cam)'))
    cy += header_h + 6
    for i, t in enumerate(tables):
        full.append(chip_frag(t, 30 + (i % 2) * ((width - 60) // 2), cy + (i // 2) * chip_step))
    write_svg("table-relationships.svg", width, int(cy + ((len(tables) + 1) // 2) * chip_step + 40),
              "Table Relationship Diagram — DBCAS (physical, generated from schema)",
              f'{len(tables)} tables, {len(fks)} directed FK edges; '
              "every edge lists source/destination columns, cardinality and ON rules", "".join(full))

    for pi, group in enumerate(pages, 1):
        body = [note, header(top, f'Khóa ngoại ({len(fks)} cạnh) — trang {pi}/{len(pages)}')]
        y = top + header_h + 24
        for f in group:
            body.append(fk_frag(f, y)); y += row_h
        y += 16
        body.append(header(y, f'Bảng ({len(tables)} bảng; legacy/retired tô màu cam)'))
        y += header_h + 6
        chips = tables[(pi - 1) * chips_per_page: pi * chips_per_page]
        for i, t in enumerate(chips):
            body.append(chip_frag(t, 30 + (i % 2) * ((width - 60) // 2), y + (i // 2) * chip_step))
        y += ((len(chips) + 1) // 2) * chip_step + 30
        write_svg(f"table-relationships-{pi}.svg", width, int(y),
                  f"Table Relationship Diagram — DBCAS ({pi}/{len(pages)})",
                  "41 bảng, 59 cạnh khóa ngoại có hướng, tên cột và cardinality", "".join(body))
    return len(pages)


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    build_context()
    n_tables, w, h, erd_pages = build_erd()
    trd_pages = build_table_relationships()
    manifest = {
        "source": "docs/qa/schema-introspection.json + docs/qa/project-facts.json + system-context-model.json",
        "tables": n_tables,
        "columns": sum(len(t["columns"]) for t in INTRO["tables"]),
        "foreign_keys": len(INTRO["foreign_keys"]),
        "indexes": len(INTRO["indexes"]),
        "enums": len(INTRO["enums"]),
        "migrations": len(INTRO["migrations"]),
        "table_names": [t["table"] for t in INTRO["tables"]],
        "column_names": sorted({c["name"] for t in INTRO["tables"] for c in t["columns"]}),
        "fk_constraints": [f["constraint"] for f in INTRO["foreign_keys"]],
        "legacy_tables": sorted(LEGACY),
        "context_nodes": [n["id"] for n in CTX["nodes"]],
        "context_flows": [f["id"] for f in CTX["flows"]],
        "compose_services": FACTS["compose_services"],
        "compose_services_all": FACTS["compose_services_all"],
        "openapi_path_count": FACTS["openapi_path_count"],
        "openapi_operation_count": FACTS["openapi_operation_count"],
        "openapi_paths": FACTS["openapi_paths"],
        "frontend_routes": FACTS["frontend_routes"],
        "admin_nav": FACTS["admin_nav"],
        "erd_size": [w, h],
        "erd_pages": erd_pages,
        "table_relationship_pages": trd_pages,
    }
    (GEN / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"generated: system-context.svg, erd.svg ({w}x{h}, {n_tables} tables), "
          f"table-relationships.svg, {erd_pages} ERD pages, {trd_pages} TRD pages, manifest.json")


if __name__ == "__main__":
    main()
