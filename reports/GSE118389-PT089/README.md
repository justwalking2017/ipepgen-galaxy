# GSE118389 / PT089 chromosome 22 pilot

This directory contains an executable-output example for iPepGen scNeo v0.5.0.
The input junction files and tumor/normal labels are the TNBC-2 demonstration
data distributed by SCASL (source commit
`1bf912435c08971b4124d6527aa3ffa31af199dc`), corresponding to PT089 in
GSE118389. Reference sequence, annotations, and proteins are GRCh38 chromosome
22 / GENCODE v48.

The run aggregated 32 labeled cells, retained 145 tumor-specific junctions,
translated 12,510 junction-spanning peptide records, removed exact normal
proteome matches, and obtained 789 MHCflurry candidates at 500 nM or better.
The complete ranked output is `consensus.tsv`; the human-readable output is
`neoantigen-report.html`.

pVACsplice was not run because the public demonstration lacks a matched
VEP-annotated VCF, BAM, and RegTools cis-splice output. SNAF was not run because
the SCASL coordinate matrix is not its required AltAnalyze UID matrix and a
matching SNAF reference bundle was unavailable. These statuses appear in the
report and must not be interpreted as failed validation.

Patient HLA typing was unavailable, so HLA-A*02:01, HLA-B*07:02 and
HLA-C*07:02 were used as exploratory common alleles. The SCASL junction genome
assembly was assumed to be GRCh38. This pilot is research-use-only and is not a
clinical or genome-wide patient analysis.
