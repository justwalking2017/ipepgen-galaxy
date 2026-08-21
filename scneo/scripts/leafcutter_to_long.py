#!/usr/bin/env python3
"""Convert per-cell LeafCutter junction files plus SCASL labels to long TSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from junctions import write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("junction_dir")
    parser.add_argument("labels_csv", help="SCASL label CSV with Run and type columns")
    parser.add_argument("counts_out")
    parser.add_argument("metadata_out")
    parser.add_argument("--cluster-column", default="type")
    parser.add_argument("--chromosome", help="Optional chromosome subset for a small reproducible pilot")
    args = parser.parse_args()
    with open(args.labels_csv, newline="", encoding="utf-8-sig") as handle:
        labels = list(csv.DictReader(handle))
    files = {path.stem: path for path in Path(args.junction_dir).glob("*.junc")}
    counts, metadata = [], []
    for row in labels:
        run = row["Run"]
        if run not in files:
            continue
        compartment = row["type"].strip().lower()
        if compartment not in {"tumor", "normal"}:
            continue
        metadata.append({"cell_id": run, "compartment": compartment, "cluster": row.get(args.cluster_column, compartment)})
        with files[run].open(encoding="utf-8") as handle:
            for line in handle:
                chrom, start, end, _, count, strand = line.rstrip("\n").split("\t")[:6]
                if args.chromosome and chrom != args.chromosome:
                    continue
                if int(count) > 0:
                    counts.append({"junction_id": f"{chrom}:{start}-{end}:{strand}", "cell_id": run, "count": count})
    if not metadata:
        raise SystemExit("No label rows had matching .junc files")
    write_tsv(args.counts_out, counts, ["junction_id", "cell_id", "count"])
    write_tsv(args.metadata_out, metadata, ["cell_id", "compartment", "cluster"])


if __name__ == "__main__":
    main()
