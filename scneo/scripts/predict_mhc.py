#!/usr/bin/env python3
"""Predict HLA-I presentation with MHCflurry or an explicit CI-only mock."""

from __future__ import annotations

import argparse
import hashlib

from junctions import read_tsv, write_tsv


def mock_score(peptide: str, allele: str) -> tuple[float, float]:
    value = int(hashlib.sha256(f"{peptide}|{allele}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 25.0 + value * 4975.0, 1.0 - value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidates")
    parser.add_argument("alleles", help="Text file, one HLA allele per line")
    parser.add_argument("output")
    parser.add_argument("--backend", choices=["mhcflurry", "mock"], default="mhcflurry")
    parser.add_argument("--max-affinity", type=float, default=500.0)
    args = parser.parse_args()
    candidates = read_tsv(args.candidates)
    with open(args.alleles, encoding="utf-8") as handle:
        alleles = [line.strip() for line in handle if line.strip() and not line.startswith("#")]
    if not alleles:
        raise SystemExit("No HLA alleles supplied")

    rows = []
    if args.backend == "mhcflurry":
        from mhcflurry import Class1PresentationPredictor
        predictor = Class1PresentationPredictor.load()
        frame = predictor.predict(peptides=[r["peptide"] for r in candidates], alleles=alleles, verbose=0)
        best = frame.sort_values(["peptide", "presentation_score"], ascending=[True, False]).groupby("peptide").first()
        scores = {p: (float(r["affinity"]), float(r["presentation_score"]), str(r["best_allele"])) for p, r in best.iterrows()}
    else:
        scores = {}
        for row in candidates:
            candidates_scores = [(mock_score(row["peptide"], allele), allele) for allele in alleles]
            (affinity, presentation), allele = max(candidates_scores, key=lambda item: item[0][1])
            scores[row["peptide"]] = (affinity, presentation, allele)

    for row in candidates:
        affinity, presentation, allele = scores[row["peptide"]]
        enriched = dict(row)
        enriched.update({"best_allele": allele, "affinity_nm": f"{affinity:.3f}", "presentation_score": f"{presentation:.6f}", "prediction_backend": args.backend})
        if affinity <= args.max_affinity:
            rows.append(enriched)
    rows.sort(key=lambda r: (-float(r["presentation_score"]), -int(r["tumor_cells"]), r["candidate_id"]))
    fields = list(rows[0]) if rows else list(candidates[0]) + ["best_allele", "affinity_nm", "presentation_score", "prediction_backend"] if candidates else ["candidate_id", "junction_id", "peptide", "best_allele", "affinity_nm", "presentation_score", "prediction_backend"]
    write_tsv(args.output, rows, fields)


if __name__ == "__main__":
    main()
