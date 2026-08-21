#!/usr/bin/env python3
"""Create junction-spanning peptides from genomic splice-flank sequences.

Coordinates use one-based exon boundaries. All three frames are evaluated because
single-cell junction evidence alone does not establish the translated isoform.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq

from junctions import read_tsv, write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("junctions")
    parser.add_argument("genome")
    parser.add_argument("output_tsv")
    parser.add_argument("output_fasta")
    parser.add_argument("--flank-nt", type=int, default=90)
    parser.add_argument("--lengths", default="8,9,10,11")
    args = parser.parse_args()

    genome = SeqIO.to_dict(SeqIO.parse(args.genome, "fasta"))
    lengths = sorted({int(x) for x in args.lengths.split(",")})
    rows, seen = [], set()
    for event in read_tsv(args.junctions):
        chrom, donor, acceptor, strand = event["chrom"], int(event["donor"]), int(event["acceptor"]), event["strand"]
        if chrom not in genome:
            raise SystemExit(f"Chromosome {chrom!r} is absent from genome FASTA")
        sequence = genome[chrom].seq
        left = sequence[max(0, donor - args.flank_nt):donor]
        right = sequence[acceptor - 1:min(len(sequence), acceptor - 1 + args.flank_nt)]
        joined = left + right
        boundary_nt = len(left)
        if strand == "-":
            joined = joined.reverse_complement()
            boundary_nt = len(right)
        for frame in range(3):
            protein = str(joined[frame:].translate())
            boundary_aa = (boundary_nt - frame) // 3
            for length in lengths:
                for start in range(max(0, boundary_aa - length + 1), min(boundary_aa, len(protein) - length) + 1):
                    peptide = protein[start:start + length]
                    if len(peptide) != length or "*" in peptide or "X" in peptide:
                        continue
                    key = (event["junction_id"], frame, peptide)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({
                        "candidate_id": f"SCN{len(rows)+1:07d}", "junction_id": event["junction_id"],
                        "peptide": peptide, "length": length, "frame": frame,
                        "tumor_cells": event["tumor_cells"], "tumor_reads": event["tumor_reads"],
                        "tumor_clusters": event["tumor_clusters"], "translation_confidence": "three_frame",
                    })
    fields = ["candidate_id", "junction_id", "peptide", "length", "frame", "tumor_cells", "tumor_reads", "tumor_clusters", "translation_confidence"]
    write_tsv(args.output_tsv, rows, fields)
    with Path(args.output_fasta).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(f">{row['candidate_id']}|{row['junction_id']}|frame={row['frame']}\n{row['peptide']}\n")


if __name__ == "__main__":
    main()
