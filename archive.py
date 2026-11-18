"""Build an offline searchable archive of matched inflation forecasts."""
import csv
import html
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load():
    return json.loads((ROOT / "data.json").read_text(encoding="utf-8"))


def evaluate(data):
    releases = {r["month"]: r for r in data["releases"]}
    output = []
    for pair in data["pairs"]:
        actual = statistics.mean(releases[m]["value"] for m in data["periods"][pair["period"]])
        seen = [r for r in data["releases"] if r["release"] <= pair["date"]]
        last = max(seen, key=lambda r: r["month"])
        row = dict(**pair, actual=actual, baseline=last["value"], baseline_month=last["month"])
        for key in ("mpc", "survey", "baseline"):
            row[key+"_error"] = abs(row[key] - actual)
        output.append(row)
    return output, {key: statistics.mean(r[key+"_error"] for r in output)
                    for key in ("mpc", "survey", "baseline")}


def chart(data, path):
    width = 620
    scale = 400 / max(data.values(), default=1) if any(data.values()) else 1
    colors = {"mpc": "#09687a", "survey": "#a4422c", "baseline": "#405269"}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="235" viewBox="0 0 {width} 235">',
           '<rect width="620" height="235" fill="#f2f6f9"/>',
           '<g font-family="sans-serif" fill="#172f41">',
           '<text x="22" y="29" font-size="20">Matched forecast error (percentage points)</text>']
    for n, (key, value) in enumerate(data.items()):
        y = 58 + n * 49
        svg.append(f'<text x="23" y="{y+19}">{key.upper()}</text>'
                   f'<rect x="122" y="{y}" width="{scale*value:.1f}" height="25" fill="{colors[key]}"/>'
                   f'<text x="{130+scale*value:.1f}" y="{y+19}">{value:.2f}</text>')
    path.write_text("\n".join(svg + ["</g></svg>"]), encoding="utf-8")


def archive(records):
    lines = []
    for row in records:
        mpc = html.escape(row["mpc_source"])
        survey = html.escape(row["survey_source"])
        lines.append(f'<tr><td>{row["date"]}</td><td>{row["period"]}</td>'
                     f'<td><a href="{mpc}">{row["mpc"]:.1f}</a></td>'
                     f'<td><a href="{survey}">{row["survey"]:.1f}</a></td>'
                     f'<td>{row["baseline"]:.2f}</td><td>{row["actual"]:.2f}</td></tr>')
    page = """<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Inflation forecast archive</title><style>body{font:1rem/1.6 system-ui;color:#17394d;max-width:65rem;margin:4rem auto;padding:0 1rem;background:#f5f8fb}
table{border-collapse:collapse;width:100%;background:white}td,th{border-bottom:1px solid #d4dde5;padding:.65rem;text-align:left}
input{font:inherit;padding:.45rem;margin:.7rem}img{max-width:100%}</style>
<h1>Inflation forecast archive</h1><p>Compare dated RBI MPC and external survey forecasts on the same targets. Values are percentages.</p>
<label>Filter by date or quarter <input type=search></label><table><thead><tr><th>Date</th><th>Target</th><th>MPC</th><th>Survey</th><th>Baseline</th><th>Actual</th></tr></thead><tbody>"""
    script = """</tbody></table><img src="errors.svg" alt="Mean absolute forecast errors by system">
<script>document.querySelector("input").addEventListener("input",event=>{
for(const row of document.querySelectorAll("tbody tr"))row.hidden=!row.textContent.toLowerCase().includes(event.target.value.trim().toLowerCase());
});</script></html>"""
    (ROOT / "index.html").write_text(page + "\n".join(lines) + script, encoding="utf-8")


def run():
    rows, scores = evaluate(load())
    with (ROOT / "overlap.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "metrics.json").write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    chart(scores, ROOT / "errors.svg")
    archive(rows)
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    run()
