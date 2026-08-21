#!/usr/bin/env python3
"""Normalize SNAF or pVACsplice output into a small evidence interchange TSV."""

from __future__ import annotations

import argparse
from pathlib import Path

from junctions import read_tsv, write_tsv


FIELDS = ["method", "status", "junction_id", "peptide", "allele", "affinity_nm", "source_file"]


def choose(row, *names):
    lowered = {key.lower().replace(" ", "_"): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower().replace(" ", "_"))
        if value not in (None, ""):
            return value
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=["snaf", "pvacsplice"])
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--disabled-reason")
    args = parser.parse_args()
    if args.disabled_reason:
        write_tsv(args.output, [{"method": args.method, "status": f"not_run: {args.disabled_reason}", "junction_id": "", "peptide": "", "allele": "", "affinity_nm": "", "source_file": ""}], FIELDS)
        return
    path = Path(args.input)
    rows = []
    for row in read_tsv(path):
        peptide = choose(row, "peptide", "mt_epitope_seq", "epitope_seq")
        if not peptide:
            continue
        rows.append({
            "method": args.method, "status": "candidate", "junction_id": choose(row, "junction_id", "uid", "index"),
            "peptide": peptide, "allele": choose(row, "hla_allele", "allele", "best_allele"),
            "affinity_nm": choose(row, "median_mt_ic50_score", "ic50", "affinity_nm"), "source_file": str(path),
        })
    if not rows:
        rows.append({"method": args.method, "status": "run_no_candidates", "junction_id": "", "peptide": "", "allele": "", "affinity_nm": "", "source_file": str(path)})
    write_tsv(args.output, rows, FIELDS)


if __name__ == "__main__":
    main()
