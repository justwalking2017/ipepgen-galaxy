#!/usr/bin/env python3
"""Remove peptides exactly present in the supplied normal reference proteome."""

from __future__ import annotations

import argparse
from Bio import SeqIO
from junctions import read_tsv, write_tsv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidates")
    parser.add_argument("proteome")
    parser.add_argument("output")
    args = parser.parse_args()
    candidates = read_tsv(args.candidates)
    candidate_peptides = {row["peptide"].upper() for row in candidates}
    lengths = {len(peptide) for peptide in candidate_peptides}
    reference_matches = set()
    for record in SeqIO.parse(args.proteome, "fasta"):
        protein = str(record.seq).upper()
        for length in lengths:
            for start in range(0, len(protein) - length + 1):
                peptide = protein[start:start + length]
                if peptide in candidate_peptides:
                    reference_matches.add(peptide)
        if len(reference_matches) == len(candidate_peptides):
            break
    rows = []
    for row in candidates:
        row["reference_match"] = "yes" if row["peptide"].upper() in reference_matches else "no"
        if row["reference_match"] == "no":
            rows.append(row)
    fields = list(rows[0]) if rows else ["candidate_id", "junction_id", "peptide", "length", "frame", "tumor_cells", "tumor_reads", "tumor_clusters", "translation_confidence", "reference_match"]
    write_tsv(args.output, rows, fields)


if __name__ == "__main__":
    main()
