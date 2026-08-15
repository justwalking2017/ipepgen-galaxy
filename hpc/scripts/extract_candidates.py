import csv, sys
from Bio import SeqIO

report, reference, out_tsv, out_fasta = sys.argv[1:]
reference_sequences = [str(r.seq).upper() for r in SeqIO.parse(reference, "fasta")]
with open(report, encoding="utf-8", errors="replace") as src:
    reader = csv.DictReader(src, delimiter="\t")
    peptide_col = next((c for c in reader.fieldnames or [] if c.lower() in {"peptide", "sequence", "stripped peptide"}), None)
    protein_col = next((c for c in reader.fieldnames or [] if "protein" in c.lower()), None)
    if not peptide_col:
        raise SystemExit("FragPipe report has no recognized peptide column")
    rows = []
    for row in reader:
        peptide = row[peptide_col].upper().replace("_", "")
        proteins = row.get(protein_col, "") if protein_col else ""
        if peptide and ("generic|" in proteins.lower() or not any(peptide in seq for seq in reference_sequences)):
            rows.append((peptide, proteins))
rows = list(dict.fromkeys(rows))
with open(out_tsv, "w", encoding="utf-8", newline="") as tab, open(out_fasta, "w", encoding="utf-8") as fasta:
    writer = csv.writer(tab, delimiter="\t"); writer.writerow(["peptide", "proteins"])
    for i, (peptide, proteins) in enumerate(rows, 1):
        writer.writerow([peptide, proteins]); fasta.write(f">candidate_{i}\n{peptide}\n")

