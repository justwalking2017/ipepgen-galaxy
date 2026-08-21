"""Shared parsing helpers for the single-cell splice neoantigen workflow."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Junction:
    junction_id: str
    chrom: str
    donor: int
    acceptor: int
    strand: str


def parse_junction_id(value: str) -> Junction:
    """Parse ``chrom:donor-acceptor:strand`` (one-based exon boundaries)."""
    chrom, coordinates, strand = value.rsplit(":", 2)
    donor, acceptor = (int(item) for item in coordinates.split("-", 1))
    if donor >= acceptor or strand not in {"+", "-"}:
        raise ValueError(f"Invalid junction: {value}")
    return Junction(value, chrom, donor, acceptor, strand)


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: str | Path, rows: list[dict], fields: list[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
