#!/usr/bin/env python3
"""Render a self-contained, auditable HTML candidate report."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from junctions import read_tsv


def table(rows, columns, limit=100):
    if not rows:
        return "<p>No rows.</p>"
    head = "".join(f"<th>{html.escape(c)}</th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(c, '')))}</td>" for c in columns) + "</tr>" for row in rows[:limit])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("consensus")
    parser.add_argument("junctions")
    parser.add_argument("snaf")
    parser.add_argument("pvacsplice")
    parser.add_argument("output")
    parser.add_argument("--metadata-json", required=True)
    args = parser.parse_args()
    candidates, junctions = read_tsv(args.consensus), read_tsv(args.junctions)
    validations = read_tsv(args.snaf) + read_tsv(args.pvacsplice)
    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
    cross = sum(row.get("cross_validated") == "yes" for row in candidates)
    strong = sum(float(row.get("affinity_nm", "inf")) <= 500 for row in candidates)
    columns = ["candidate_id", "junction_id", "peptide", "best_allele", "affinity_nm", "presentation_score", "tumor_cells", "tumor_reads", "supporting_methods", "cross_validated"]
    validation_columns = ["method", "status", "junction_id", "peptide", "allele", "affinity_nm"]
    style = """body{font-family:system-ui;margin:2rem;color:#172033}h1,h2{color:#173f5f}.cards{display:flex;gap:1rem;flex-wrap:wrap}.card{padding:1rem 1.4rem;background:#eef6f8;border-radius:10px;min-width:150px}.n{font-size:2rem;font-weight:700}table{border-collapse:collapse;width:100%;font-size:.82rem}th,td{border:1px solid #ccd6dd;padding:.4rem;text-align:left}th{background:#173f5f;color:white;position:sticky;top:0}.warn{background:#fff4ce;padding:1rem;border-left:5px solid #d99b00}code{background:#edf1f3;padding:.1rem .3rem}.scroll{overflow:auto;max-height:650px}footer{margin-top:2rem;color:#536471} """
    content = f"""<!doctype html><html><head><meta charset='utf-8'><title>iPepGen scNeo report</title><style>{style}</style></head><body>
<h1>iPepGen scNeo candidate report</h1><p><b>Dataset:</b> {html.escape(metadata['dataset'])}<br><b>Sample:</b> {html.escape(metadata['sample'])}<br><b>Source:</b> <a href='{html.escape(metadata['source_url'])}'>{html.escape(metadata['accession'])}</a><br><b>Genome:</b> {html.escape(metadata['genome'])}</p>
<div class='warn'><b>Research-use-only.</b> These are computational candidates, not clinically validated neoantigens. The mock predictor, if shown in the table, is non-scientific and must not be used for biological conclusions.</div>
<div class='cards'><div class='card'><div class='n'>{len(junctions)}</div>tumor-specific junctions</div><div class='card'><div class='n'>{len(candidates)}</div>ranked candidates</div><div class='card'><div class='n'>{strong}</div>affinity ≤500 nM</div><div class='card'><div class='n'>{cross}</div>cross-validated</div></div>
<h2>Cross-validation status</h2>{table(validations, validation_columns)}
<h2>Top candidates</h2><div class='scroll'>{table(candidates, columns)}</div>
<h2>Methods and interpretation</h2><p>SCASL/LeafCutter junction evidence was aggregated across labeled tumor and normal single cells. Unannotated tumor-supported events were translated in three frames, exact reference-proteome matches were removed, and HLA presentation was scored. SNAF is a junction-matrix validation branch. pVACsplice is only valid when matched VEP-annotated VCF, BAM, RegTools output, genome and GTF are available.</p>
<p>Three-frame candidates have uncertain coding frame. Confirm priority events using transcript-aware assembly, independent RNA evidence, population normal-tissue junctions, immunopeptidomics and T-cell assays.</p>
<h2>Provenance</h2><pre>{html.escape(json.dumps(metadata, indent=2))}</pre><footer>Generated {datetime.now(timezone.utc).isoformat()} by iPepGen scNeo.</footer></body></html>"""
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
