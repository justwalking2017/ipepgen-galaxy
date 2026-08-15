import csv, sys

psm_path, blast_path, output = sys.argv[1:]
non_novel = set()
with open(blast_path, encoding="utf-8") as handle:
    for row in csv.reader(handle, delimiter="\t"):
        if len(row) >= 4 and float(row[1]) >= 100.0 and int(row[2]) >= int(row[3]):
            non_novel.add(row[0])
with open(psm_path, encoding="utf-8", errors="replace") as src:
    reader = csv.DictReader(src, delimiter="\t")
    fields = reader.fieldnames or []
    peptide_col = next((c for c in fields if c.lower() in {"peptide", "sequence", "peptide_sequence"}), None)
    if not peptide_col:
        raise SystemExit("PepQuery2 psm_rank file has no recognized peptide column")
    with open(output, "w", encoding="utf-8", newline="") as dst:
        writer = csv.writer(dst, delimiter="\t"); writer.writerow(["peptide", "pepquery_confident", "blast_novel"])
        for row in reader:
            peptide = row[peptide_col]
            confidence = next((row[c] for c in fields if "confident" in c.lower()), "Yes")
            if confidence.lower() in {"yes", "true", "1"} and peptide not in non_novel:
                writer.writerow([peptide, confidence, "Yes"])

