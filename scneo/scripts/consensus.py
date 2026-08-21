#!/usr/bin/env python3
"""Merge native predictions with optional SNAF and pVACsplice evidence."""

from __future__ import annotations

import argparse
from collections import defaultdict

from junctions import read_tsv, write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary")
    parser.add_argument("snaf")
    parser.add_argument("pvacsplice")
    parser.add_argument("output")
    args = parser.parse_args()
    external = defaultdict(set)
    for path in (args.snaf, args.pvacsplice):
        for row in read_tsv(path):
            if row.get("status") == "candidate" and row.get("peptide"):
                external[row["peptide"]].add(row["method"])
    rows = []
    for row in read_tsv(args.primary):
        methods = {"ipepgen-scneo"} | external.get(row["peptide"], set())
        enriched = dict(row)
        enriched["supporting_methods"] = ",".join(sorted(methods))
        enriched["method_count"] = len(methods)
        enriched["cross_validated"] = "yes" if len(methods) > 1 else "no"
        rows.append(enriched)
    fields = list(rows[0]) if rows else ["candidate_id", "junction_id", "peptide", "supporting_methods", "method_count", "cross_validated"]
    write_tsv(args.output, rows, fields)


if __name__ == "__main__":
    main()
