import csv, re, sys

source, target = sys.argv[1:]
with open(source, encoding="utf-8") as handle, open(target, "w", encoding="utf-8") as out:
    for n, row in enumerate(csv.DictReader(handle, delimiter="\t"), 1):
        value = row.get("peptide_sequence", "")
        if not value or value == "." or "|" not in value:
            continue
        left, right = value.split("|", 1)
        peptide = re.sub(r"\*.*$", "", left + right).upper()
        pos = max(0, len(left) - 8)
        peptide = peptide[pos:pos + 16] if row.get("reading_frame") == "in-frame" else peptide[pos:]
        if peptide:
            gene1 = re.split(r"[(,]", row.get("gene1", "NA"))[0]
            gene2 = re.split(r"[(,]", row.get("gene2", "NA"))[0]
            bp = f"{row.get('breakpoint1','NA')}_{row.get('breakpoint2','NA')}"
            out.write(f">generic|fusion_{gene1}_{gene2}__{n}__{bp}\n{peptide}\n")

