import csv, sys
import pandas as pd
from mhcflurry import Class1PresentationPredictor

verified, allele_file, output = sys.argv[1:]
with open(verified, encoding="utf-8") as handle:
    peptides = [row["peptide"] for row in csv.DictReader(handle, delimiter="\t")]
with open(allele_file, encoding="utf-8") as handle:
    alleles = [line.strip() for line in handle if line.strip()]
if not peptides or not alleles:
    pd.DataFrame(columns=["peptide", "best_allele", "affinity", "presentation_score"]).to_csv(output, sep="\t", index=False)
else:
    predictor = Class1PresentationPredictor.load()
    result = predictor.predict(peptides=peptides, alleles=alleles, verbose=0)
    result.sort_values(["peptide", "presentation_score"], ascending=[True, False]).groupby("peptide", as_index=False).head(1).to_csv(output, sep="\t", index=False)

