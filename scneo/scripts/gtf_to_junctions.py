#!/usr/bin/env python3
"""Extract annotated intron boundaries from exon records in a GTF."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict


TRANSCRIPT = re.compile(r'transcript_id "([^"]+)"')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gtf")
    parser.add_argument("output")
    args = parser.parse_args()
    transcripts = defaultdict(list)
    with open(args.gtf, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 or fields[2] != "exon":
                continue
            match = TRANSCRIPT.search(fields[8])
            if match:
                transcripts[(match.group(1), fields[0], fields[6])].append((int(fields[3]), int(fields[4])))
    junctions = set()
    for (_, chrom, strand), exons in transcripts.items():
        exons.sort()
        for left, right in zip(exons, exons[1:]):
            if left[1] < right[0] - 1:
                junctions.add(f"{chrom}:{left[1]}-{right[0]}:{strand}")
    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        for junction in sorted(junctions):
            handle.write(junction + "\n")


if __name__ == "__main__":
    main()
