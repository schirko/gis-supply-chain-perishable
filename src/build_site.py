"""Build the public project site (the portfolio page for this project).

Run from the project root:   python -m src.build_site

What it does
  1. Redraws the front-page charts from data/processed/bread_daily.csv.
  2. Fills the headline numbers (src/site_facts.json plus the data) into src/site_template.html.
  3. Exports every notebook that has saved outputs as an HTML page.
       - Placeholder explanation cells ("Fill in together") are left out, and that notebook is
         tagged "in progress" on the front page.
       - A notebook with an error output or with code cells never run is NOT published (a warning is printed).
  4. Turns the project docs (decision log, forecast process notes) into pages.
  5. Adds a "<- Perishable Inventory Optimizer" back bar and a noindex meta tag to every page.

Where it writes: SITE_DIR from .env (the portfolio folder, e.g.
B:\\_Dev\\Python\\Schirko\\scott\\gis-supply-chain\\perishable). Without it, the git-ignored site/ folder.
Before building: Run All in each notebook and save (Ctrl+S), so the outputs are in the file.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import shutil
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/schirko/gis-supply-chain-perishable"
PROJECT_NAME = "Perishable Inventory Optimizer"
PLOTLY_JS = "https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"
PLACEHOLDER = "Fill in together"
GENERATED = ["index.html", "images", "notebooks", "docs", "figures"]  # only these are cleaned before a build

DOCS = [  # (source file, output page, link text)
    ("docs/decision_log.md", "DECISIONS", "Every decision and why"),
    ("docs/forecast_process_notes.md", "FORECAST_PROCESS", "How the forecast was built (process notes)"),
]
FIGURES = [("docs/figures/service_areas_map.html", "Warehouse service-area map")]
BLURBS = {
    "01": "Checking the Kaggle files: gaps, zero-sales days and what a sale represents.",
    "02": "Locating every store city, checking it against its province, and drawing the maps.",
    "03": "Assigning stores to four warehouse regions and choosing the first product family.",
    "04": "Splitting by time, setting baselines, and forecasting bread and bakery with gradient boosting.",
}


# ---------------------------------------------------------------- setup
def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def site_dir() -> Path:
    raw = os.environ.get("SITE_DIR", "").strip()
    return Path(raw) if raw else ROOT / "site"


BACKBAR_LINK = '<link rel="stylesheet" href="/scott/backbar.css">'
BACKBAR = """<div class="sx-backbar">
  <a class="sx-back" href="/scott/">
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
    Portfolio
  </a>
  <span class="sx-crumb">Perishable Inventory Optimizer</span>
  <span class="sx-links"><a href="/scott/gis-supply-chain/perishable/">Project page</a><a href="/scott/gis-supply-chain/perishable/#notebooks">Notebooks</a><a href="/scott/gis-supply-chain/perishable/docs/DECISIONS.html">Docs</a></span>
</div>"""
# The portfolio owns /scott/backbar.css and the .sx- classes: link to it, do not copy or restyle it.
NOINDEX = '<meta name="robots" content="noindex, nofollow">'


def decorate(page: str, depth: int, banner: str = "") -> str:
    """Add noindex, the shared portfolio back-bar stylesheet and the back bar. (depth is kept for callers; the bar uses absolute /scott/ paths.)"""
    head_add = (NOINDEX if 'name="robots"' not in page else "") + BACKBAR_LINK
    page = re.sub(r"<head[^>]*>", lambda m: m.group(0) + head_add, page, count=1, flags=re.I)
    return re.sub(r"<body[^>]*>", lambda m: m.group(0) + BACKBAR + banner, page, count=1, flags=re.I)


# ---------------------------------------------------------------- charts
def draw_charts(out: Path, facts: dict, df) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    colors = {"Quito": "#2E6A4C", "Guayaquil": "#2F6690", "Cuenca": "#A87613", "Santo Domingo": "#9A3B2E"}

    # 1. demand by warehouse, weekly mean, split shaded
    d = df.copy()
    d["date"] = d["date"].astype("datetime64[ns]")
    fig, ax = plt.subplots(figsize=(10, 4.4), dpi=150)
    for wh, g in d.groupby("warehouse"):
        w = g.set_index("date")["units_per_open_store"].resample("W").mean()
        ax.plot(w.index, w.values, label=wh, color=colors.get(wh), lw=1.6)
    for sp, col in (("validation", "#E3F0E8"), ("test", "#F6EAD9")):
        s = d[d["split"] == sp]["date"]
        if len(s):
            ax.axvspan(s.min(), s.max(), color=col, alpha=.9, zorder=0)
            ax.text(s.min(), ax.get_ylim()[1], f" {sp}", va="top", fontsize=9, color="#555",
                    rotation=90 if sp == "validation" else 0, ha="right" if sp == "validation" else "left")
    ax.set_ylabel("Units per open store (weekly mean)")
    ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(.5, 1.0))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(img / "demand.png")
    plt.close(fig)

    # 2. test error by method
    names = ["Seasonal naive\n(repeat last week)", "Median of the\nlast 8 weeks", "Gradient boosting\n(the model)"]
    vals = [facts["wape_seasonal_naive"], facts["wape_median8"], facts["wape_model"]]
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    bars = ax.bar(names, vals, color=["#9aa39e", "#9aa39e", "#2E6A4C"], width=.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + .1, f"{v:.2f}%", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average miss (WAPE, %)")
    ax.set_ylim(0, max(vals) * 1.2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(img / "error.png")
    plt.close(fig)


# ---------------------------------------------------------------- notebooks
def nb_title(nb) -> str:
    for c in nb.cells:
        if c.cell_type == "markdown":
            m = re.match(r"\s*#\s+(.*)", c.source)
            if m:
                return re.sub(r"^Notebook\s*\d+\s*:\s*", "", m.group(1)).strip()
    return "Notebook"


def nb_status(nb) -> tuple[str, str]:
    """('ok'|'in_progress'|'skip', reason)"""
    code = [c for c in nb.cells if c.cell_type == "code" and c.source.strip()]
    if any(o.get("output_type") == "error" for c in code for o in c.get("outputs", [])):
        return "skip", "a cell has an error output"
    if any(c.get("execution_count") is None for c in code):
        return "skip", "some code cells were never run (Run All, then Ctrl+S)"
    if any(PLACEHOLDER in c.source for c in nb.cells if c.cell_type == "markdown"):
        return "in_progress", "explanations still being written"
    return "ok", ""


def plotly_to_html(nb) -> bool:
    found = False
    for c in nb.cells:
        for i, o in enumerate(c.get("outputs", [])):
            data = o.get("data", {}) if o.get("output_type") in ("display_data", "execute_result") else {}
            fig = data.get("application/vnd.plotly.v1+json")
            if fig is None:
                continue
            found = True
            uid = f"plt-{id(o)}"
            payload = json.dumps(fig).replace("</", "<\\/")
            div = (f'<div id="{uid}" style="width:100%;min-height:420px"></div><script>(function(){{var f={payload};'
                   f'Plotly.newPlot("{uid}",f.data,f.layout||{{}},Object.assign({{responsive:true}},f.config||{{}}));}})();</script>')
            c["outputs"][i] = {"output_type": "display_data", "metadata": {}, "data": {"text/html": div}}
    return found


def export_notebooks(out: Path) -> list[dict]:
    import nbformat
    from nbconvert import HTMLExporter

    nbdir = out / "notebooks"
    nbdir.mkdir(parents=True, exist_ok=True)
    items = []
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        status, why = nb_status(nb)
        num = path.name.split("_")[0]
        if status == "skip":
            print(f"  SKIPPED {path.name}: {why}")
            continue
        banner = ""
        if status == "in_progress":
            nb.cells = [c for c in nb.cells if not (c.cell_type == "markdown" and PLACEHOLDER in c.source)]
            banner = ('<div style="font:14px/1.5 Inter,system-ui,sans-serif;padding:10px 20px;background:#F6EAD9;color:#74460F">'
                      '<b>Work in progress.</b> The code and results are final for now; the written explanations '
                      'for each step are still being added.</div>')
        has_plotly = plotly_to_html(nb)
        body, _ = HTMLExporter(template_name="lab").from_notebook_node(nb)
        if has_plotly:
            body = body.replace("</head>", f'<script src="{PLOTLY_JS}"></script></head>', 1)
        page = decorate(body, 1, banner)
        (nbdir / f"{path.stem}.html").write_text(page, encoding="utf8")
        items.append({"file": path.stem, "num": num, "title": nb_title(nb), "status": status,
                      "blurb": BLURBS.get(num, "")})
        print(f"  notebook {path.name} -> {status}")
    return items


# ---------------------------------------------------------------- docs
DOC_CSS = """body{margin:0;background:#faf8f5;color:#1f1b18;font:17px/1.65 Inter,system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 20px 64px}h1,h2,h3{font-family:Fraunces,Georgia,serif;line-height:1.2}
h2{margin-top:40px}a{color:#2E6A4C}code{background:#efece6;padding:1px 5px;border-radius:4px;font-size:.92em}
pre{background:#efece6;padding:12px;border-radius:8px;overflow:auto}table{border-collapse:collapse;margin:16px 0;display:block;overflow:auto}
th,td{border:1px solid #e6e0d8;padding:6px 10px;text-align:left}th{background:#f1efe9}blockquote{margin:16px 0;padding:2px 16px;border-left:4px solid #2E6A4C;color:#5f5852}"""


def fix_link(href: str, nb_done: set[str]) -> str:
    if re.match(r"^(https?:|#|mailto:)", href):
        return href
    clean = href.split("#")[0].lstrip("./")
    m = re.match(r"notebooks/(.+)\.ipynb$", clean)
    if m and m.group(1) in nb_done:
        return f"{m.group(1)}.html"
    for src, page, _ in DOCS:
        if clean == src:
            return f"{page}.html"
    return f"{GITHUB}/blob/master/{clean}"


def export_docs(out: Path, nb_done: set[str]) -> list[tuple[str, str]]:
    import markdown

    docdir = out / "docs"
    docdir.mkdir(parents=True, exist_ok=True)
    links = []
    for src, page, text in DOCS:
        p = ROOT / src
        if not p.exists():
            print(f"  missing doc {src}")
            continue
        md = p.read_text(encoding="utf8")
        body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
        body = re.sub(r'href="([^"]+)"', lambda m: f'href="{fix_link(m.group(1), nb_done)}"', body)
        title = re.search(r"^#\s+(.*)", md, re.M)
        title = html.escape(title.group(1) if title else text)
        page_html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
                     f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>'
                     f'<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;600&display=swap" rel="stylesheet">'
                     f'<style>{DOC_CSS}</style></head><body><main>{body}</main></body></html>')
        (docdir / f"{page}.html").write_text(decorate(page_html, 1), encoding="utf8")
        links.append((f"docs/{page}.html", text))
        print(f"  doc {src} -> docs/{page}.html")
    return links


def export_figures(out: Path) -> list[tuple[str, str]]:
    figdir = out / "figures"
    links = []
    for src, text in FIGURES:
        p = ROOT / src
        if not p.exists():
            continue
        figdir.mkdir(parents=True, exist_ok=True)
        (figdir / p.name).write_text(decorate(p.read_text(encoding="utf8"), 1), encoding="utf8")
        links.append((f"figures/{p.name}", text))
        print(f"  figure {src}")
    return links


# ---------------------------------------------------------------- main
def main() -> int:
    import pandas as pd

    load_env()
    out = site_dir()
    # Standing rule: this project writes ONLY its own folder (scott/gis-supply-chain/perishable/) and never the
    # portfolio's scott/index.html or styles.css, which the portfolio project owns. Refuse a SITE_DIR that looks like
    # the portfolio root so a wrong .env cannot overwrite or clean it.
    if out.name.lower() == "scott" or (out / "styles.css").exists() or (out / "backbar.css").exists():
        print(f"Refusing to build into {out}: it looks like the portfolio root. Use the project folder (see .env.example).")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    for name in GENERATED:  # clean only what this script generates
        target = out / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    print(f"Building site into {out}")

    facts = json.loads((ROOT / "src" / "site_facts.json").read_text(encoding="utf8"))
    csv = ROOT / "data" / "processed" / "bread_daily.csv"
    if not csv.exists():
        print("data/processed/bread_daily.csv is missing: run notebook 04 Step 4 first.")
        return 1
    df = pd.read_csv(csv)

    draw_charts(out, facts, df)
    items = export_notebooks(out)
    done = {i["file"] for i in items}
    doc_links = export_docs(out, done) + export_figures(out)

    nb_items = "\n".join(
        f'<li><a href="notebooks/{i["file"]}.html"><span class="num">{i["num"]}</span>'
        f'<span class="nbtitle">{html.escape(i["title"])}</span>'
        f'{"<span class=tag>in progress</span>" if i["status"] == "in_progress" else ""}</a>'
        f'<span class="blurb">{html.escape(i["blurb"])}</span></li>' for i in items)
    links_html = " · ".join(f'<a href="{h}">{html.escape(t)}</a>' for h, t in doc_links)

    stores = facts["stores_by_warehouse"]
    values = {
        "status_line": facts["status_line"],
        "stores_total": sum(stores.values()),
        "warehouse_count": len(stores),
        "warehouse_list": ", ".join(f"{k} ({v})" for k, v in stores.items()),
        "wape_model": f'{facts["wape_model"]:.2f}'.rstrip("0").rstrip("."),
        "wape_median8": f'{facts["wape_median8"]:.2f}',
        "wape_naive": f'{facts["wape_seasonal_naive"]:.2f}',
        "improvement": round(100 * (1 - facts["wape_model"] / facts["wape_median8"])),
        "test_days": facts["test_days"],
        "test_window": facts["test_window"],
        "bias": f'{facts["bias_model_pct"]:.2f}',
        "bias_median8": f'{facts["bias_median8_pct"]:.2f}',
        "bias_naive": f'{facts["bias_naive_pct"]:.2f}',
        "wape_by_wh": ", ".join(f"{k} {v:.2f}%" for k, v in facts["wape_by_warehouse"].items()),
        "n_days": f"{pd.to_datetime(df['date']).nunique():,}",
        "date_first": str(df["date"].min()),
        "date_last": str(df["date"].max()),
        "notebook_items": nb_items,
        "doc_links": links_html,
        "built_on": dt.date.today().strftime("%B %d, %Y").replace(" 0", " "),
    }
    tpl = string.Template((ROOT / "src" / "site_template.html").read_text(encoding="utf8"))
    (out / "index.html").write_text(tpl.substitute(values), encoding="utf8")
    print(f"Done: {out / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
