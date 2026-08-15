import argparse
from Bio import SeqIO
from Bio.Seq import Seq

p = argparse.ArgumentParser()
p.add_argument("input"); p.add_argument("output"); p.add_argument("--min-aa", type=int, default=10)
a = p.parse_args()
with open(a.output, "w", encoding="utf-8") as out:
    for record in SeqIO.parse(a.input, "fasta"):
        seq = str(record.seq).upper()
        for strand, dna in (("+", seq), ("-", str(Seq(seq).reverse_complement()))):
            for frame in range(3):
                aa = str(Seq(dna[frame:]).translate(to_stop=False))
                for part, peptide in enumerate(aa.split("*"), 1):
                    if len(peptide) >= a.min_aa:
                        out.write(f">generic|transcript_{record.id}|strand={strand}|frame={frame}|part={part}\n{peptide}\n")

