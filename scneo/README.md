# iPepGen scNeo: single-cell splice-derived neoantigens

`scneo/` is a Galaxy-free Snakemake workflow for prioritizing candidate HLA-I
neoantigens created by tumor-specific splice junctions observed in single-cell
RNA sequencing. It is designed for Slurm and Singularity/Apptainer.

## What it does

1. Aggregates cell-level junction counts while retaining cell clusters.
2. Removes annotated junctions and events observed in normal cells.
3. Constructs strand-aware sequence across each junction and translates all
   three possible frames.
4. Enumerates 8–11 aa peptides that cross the junction.
5. Removes exact matches to a supplied normal reference proteome.
6. Predicts patient-specific HLA-I presentation with MHCflurry and ranks hits.
7. Optionally normalizes pVACsplice and SNAF results, builds a peptide-level
   consensus table, and renders a self-contained HTML report.

SCASL 1.0.0 is supplied as a pinned optional container because it can generate
and cluster single-cell splice-junction matrices from BAM or STAR `SJ.out.tab`
files. SCASL identifies differential splicing; it does **not** translate events
or predict neoantigens. The downstream steps in this workflow are therefore
implemented explicitly and expose their evidence in TSV files.

## Inputs

The junction table is a long TSV:

```text
junction_id       cell_id count
chr1:100-201:+    AAAC... 4
```

Coordinates are one-based exon boundaries. Cell metadata must contain
`cell_id`, `compartment` (`tumor` or `normal`), and optionally `cluster`.
HLA alleles are one per line. Clinical HLA typing is preferred; RNA-derived
typing can be used when its uncertainty is retained in interpretation.

Convert SCASL and reference files when needed:

```bash
python scneo/scripts/scasl_matrix_to_long.py process_result/junc_matrix.csv junction_counts.tsv
python scneo/scripts/gtf_to_junctions.py gencode.v48.annotation.gtf gencode.v48.junctions.txt
```

Copy and edit the configuration:

```bash
cp scneo/config/config.example.yaml scneo-config.yaml
snakemake --snakefile scneo/Snakefile \
  --configfile scneo-config.yaml \
  --workflow-profile scneo/config/slurm
```

Build the images on a Linux build node:

```bash
mkdir -p containers
apptainer build containers/ipepgen-scasl.sif scneo/containers/ipepgen-scasl.def
apptainer build containers/ipepgen-scneo-helpers.sif scneo/containers/ipepgen-scneo-helpers.def
apptainer build containers/ipepgen-scneo-mhcflurry.sif scneo/containers/ipepgen-scneo-mhcflurry.def
apptainer build containers/ipepgen-snaf.sif scneo/containers/ipepgen-snaf.def
apptainer build containers/ipepgen-pvacsplice.sif scneo/containers/ipepgen-pvacsplice.def
```

## Cross-validation

Set `validation.snaf.enabled` or `validation.pvacsplice.enabled` in the YAML
configuration and provide the corresponding command template and input files.
Both branches are optional: disabled or inapplicable methods are recorded in
the report instead of being silently treated as negative evidence.

SNAF expects its AltAnalyze-style gene/exon UID junction-count matrix, HLA
alleles, and matching reference bundle. pVACsplice requires a VEP-annotated
VCF, matched BAM, RegTools `cis-splice-effects` output, reference FASTA and GTF.
Consequently, neither tool can scientifically validate an arbitrary coordinate
matrix alone. The workflow normalizes their native TSV results and considers a
candidate cross-validated only when the same peptide is supported by at least
two methods.

The checked-in pilot report is
[`reports/GSE118389-PT089/neoantigen-report.html`](../reports/GSE118389-PT089/neoantigen-report.html).
It uses real SCASL junction files and real MHCflurry predictions; its assumed
HLA alleles and chromosome-only scope make it a workflow demonstration, not a
patient result.

For a local smoke test (the mock backend is deterministic and is **not** a
scientific binding predictor):

```bash
snakemake --snakefile scneo/Snakefile \
  --configfile scneo/tests/config.yaml --cores 1
```

## Multiple-myeloma dataset

The 2026 disease-spectrum study places raw scRNA/scTCR/scBCR FASTQs under EGA
accession `EGAD50000002519`; access requires authorization. Its listed GEO
accessions (`GSE124310`, `GSE161801`, `GSE223060`, `GSE271107`, `GSE232988`)
provide expression resources, but a processed gene-count matrix cannot recover
splice junctions. Use authorized FASTQ, cell BAM, or STAR junction output for
discovery. The example config records these accessions without redistributing
human data.

## Interpretation and limitations

- Candidates are predictions, not validated antigens. Confirmation requires
  orthogonal bulk RNA support, matched-normal filtering, immunopeptidomics,
  and/or T-cell assays.
- Three-frame translation is intentionally conservative when a full isoform is
  unavailable. `translation_confidence=three_frame` prevents it being mistaken
  for transcript-aware ORF evidence.
- Exact proteome subtraction does not replace population-scale normal tissue
  junction filtering (for example GTEx) or immunogenicity validation.
- Sparse 3′-tag scRNA-seq often has weak junction coverage. Full-length
  Smart-seq2/3 or aggregated cell BAMs are better suited to discovery.
- The built-in production predictor is currently HLA-I MHCflurry. HLA-II and
  licensed NetMHCpan integrations can be added without changing upstream files.

SCASL is Apache-2.0 licensed. MHCflurry is Apache-2.0 licensed. Review upstream
licenses and institutional human-data policies before use.
