#!/usr/bin/env python3
"""Aggregate cell-level junction evidence and select tumor-specific events."""

from __future__ import annotations

import argparse
from collections import defaultdict

from junctions import parse_junction_id, read_tsv, write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("counts", help="TSV: junction_id, cell_id, count")
    parser.add_argument("metadata", help="TSV: cell_id, compartment[, cluster]")
    parser.add_argument("output")
    parser.add_argument("--annotated", help="Optional file with one reference junction ID per line")
    parser.add_argument("--min-tumor-cells", type=int, default=3)
    parser.add_argument("--min-tumor-reads", type=int, default=5)
    parser.add_argument("--max-normal-cells", type=int, default=0)
    args = parser.parse_args()

    metadata = {r["cell_id"]: r for r in read_tsv(args.metadata)}
    annotated = set()
    if args.annotated:
        with open(args.annotated, encoding="utf-8") as handle:
            annotated = {line.strip() for line in handle if line.strip() and not line.startswith("#")}

    per_junction: dict[str, dict[str, object]] = defaultdict(
        lambda: {"tumor_cells": set(), "normal_cells": set(), "tumor_reads": 0, "normal_reads": 0, "clusters": set()}
    )
    for row in read_tsv(args.counts):
        cell = row["cell_id"]
        if cell not in metadata:
            raise SystemExit(f"Cell {cell!r} is absent from metadata")
        count = int(float(row["count"]))
        if count <= 0:
            continue
        compartment = metadata[cell]["compartment"].lower()
        if compartment not in {"tumor", "normal"}:
            raise SystemExit(f"compartment must be tumor or normal, got {compartment!r}")
        stats = per_junction[row["junction_id"]]
        stats[f"{compartment}_cells"].add(cell)
        stats[f"{compartment}_reads"] += count
        if compartment == "tumor":
            stats["clusters"].add(metadata[cell].get("cluster", "unassigned") or "unassigned")

    rows = []
    for junction_id, stats in sorted(per_junction.items()):
        junction = parse_junction_id(junction_id)
        tumor_cells = len(stats["tumor_cells"])
        normal_cells = len(stats["normal_cells"])
        if junction_id in annotated:
            continue
        if tumor_cells < args.min_tumor_cells or stats["tumor_reads"] < args.min_tumor_reads:
            continue
        if normal_cells > args.max_normal_cells:
            continue
        rows.append({
            "junction_id": junction_id, "chrom": junction.chrom, "donor": junction.donor,
            "acceptor": junction.acceptor, "strand": junction.strand,
            "tumor_cells": tumor_cells, "tumor_reads": stats["tumor_reads"],
            "normal_cells": normal_cells, "normal_reads": stats["normal_reads"],
            "tumor_clusters": ",".join(sorted(stats["clusters"])),
        })
    fields = ["junction_id", "chrom", "donor", "acceptor", "strand", "tumor_cells", "tumor_reads", "normal_cells", "normal_reads", "tumor_clusters"]
    write_tsv(args.output, rows, fields)


if __name__ == "__main__":
    main()
