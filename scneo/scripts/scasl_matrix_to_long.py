#!/usr/bin/env python3
"""Convert a SCASL junction matrix (junctions x cells) to the workflow long TSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from junctions import parse_junction_id, write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", help="SCASL junc_matrix.csv or compatible matrix")
    parser.add_argument("output")
    args = parser.parse_args()
    with Path(args.matrix).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(header) < 2:
            raise SystemExit("Junction matrix needs a junction-ID column and at least one cell")
        cells = header[1:]
        result = []
        for row in reader:
            if not row:
                continue
            parse_junction_id(row[0])
            for cell, value in zip(cells, row[1:]):
                count = int(float(value or 0))
                if count > 0:
                    result.append({"junction_id": row[0], "cell_id": cell, "count": count})
    write_tsv(args.output, result, ["junction_id", "cell_id", "count"])


if __name__ == "__main__":
    main()
