import csv, glob, os, sys

files = glob.glob(os.path.join(sys.argv[1], "**", "*_result.tsv"), recursive=True)
if not files:
    raise SystemExit("OptiType result TSV was not found")
with open(files[0], encoding="utf-8") as src:
    row = next(csv.DictReader(src, delimiter="\t"))
alleles = []
for locus in ("A", "B", "C"):
    for i in (1, 2):
        value = row.get(f"{locus}{i}")
        if value:
            alleles.append(value if value.startswith("HLA-") else f"HLA-{value}")
with open(sys.argv[2], "w", encoding="utf-8") as out:
    out.write("\n".join(dict.fromkeys(alleles)) + "\n")

