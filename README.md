# iPepGen Galaxy workflow bundle

A reproducible bundle of the official Galaxy workflows described in the 2026 iPepGen paper, a command-line client, and a Snakemake DAG for remote execution on Galaxy.

This repository does **not** reimplement the scientific algorithms or redistribute FragPipe components. The `.ga` files preserve the exact Galaxy tool versions and parameter mappings published by the authors. Full analysis runs on a Galaxy server with the referenced tools and sufficient compute.

## Included workflows

| Stage | Workflow |
|---|---|
| 1 | Gene-fusion database generation |
| 1 | General non-reference database generation |
| 2 | FragPipe candidate discovery |
| 3 | PepQuery2 verification |
| 4 | PepPointer annotation |
| 5 | HLA genotyping |
| 5 | IEDB peptide–HLA binding prediction |
| End-to-end | One-Click iPepGen workflow |

## Quick start

Requirements: Python 3.10+ and a Galaxy account/API key for import or execution.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
ipepgen list
ipepgen validate
```

Import the One-Click workflow into Galaxy Europe:

```bash
export GALAXY_URL=https://usegalaxy.eu
export GALAXY_API_KEY=your-api-key
ipepgen import workflows/one-click.ga
```

The import command prints the Galaxy workflow ID. Upload input datasets in Galaxy, create a JSON map from input step IDs to history dataset/collection IDs, then invoke it:

```bash
ipepgen run WORKFLOW_ID --inputs inputs.json --history-name "my iPepGen run"
```

`examples/inputs.example.json` shows the Galaxy API mapping shape. Input step IDs differ by workflow; inspect them in the Galaxy workflow editor after import.

## Docker

```bash
docker build -t ipepgen-galaxy .
docker run --rm ipepgen-galaxy validate
```

## Snakemake workflow

Version 0.2 added Galaxy-backed Snakemake orchestration. Version 0.3 adds a separate Galaxy-free HPC implementation in [`hpc/`](hpc/) that invokes native tools inside Singularity/Apptainer images and includes a Slurm executor profile.

```bash
pip install -e ".[workflow]"
cp workflow/config/config.example.yaml config.yaml
# Replace placeholders with local paths or Galaxy dataset/collection IDs.
export GALAXY_API_KEY=your-api-key
snakemake --snakefile workflow/Snakefile --configfile config.yaml --cores 2
```

See [`workflow/README.md`](workflow/README.md) for the DAG modes and configuration details.

For a fully local HPC run with no Galaxy or BioBlend calls, use [`hpc/Snakefile`](hpc/Snakefile) and follow [`hpc/README.md`](hpc/README.md). FragPipe remains user-supplied because its academic/non-commercial license does not permit bundling it into the public release image.

Pass credentials only at runtime:

```bash
docker run --rm \
  -e GALAXY_URL=https://usegalaxy.eu \
  -e GALAXY_API_KEY \
  ipepgen-galaxy import workflows/one-click.ga
```

## Compute and licensing caveats

The paper reports that major stages need substantially more resources than a laptop: Module 1 can require 10 CPUs, 17+ GB RAM and roughly 30 hours; the FragPipe search used 16 CPUs and 250 GB RAM. Use Galaxy Europe or a suitably configured institutional Galaxy/HPC installation.

MSFragger and IonQuant are available under separate academic/non-commercial terms. This repository contains workflow definitions only; users must accept and comply with upstream licenses. The bundled workflows are attributed to the original iPepGen/GalaxyP authors and were published under CC BY 4.0. Repository helper code is MIT licensed.

## Reproducibility and releases

Every push and pull request validates all eight Galaxy exports, runs unit tests, and builds the container. Tags matching `v*` build Python distributions, package the `.ga` workflows, publish a GHCR image, and attach the artifacts to a GitHub Release.

## Citation and data

Please cite Mehta et al., “iPepGen: a modular, immunopeptidogenomic analysis pipeline for discovery, verification, and prioritization of cancer peptide neoantigen candidates,” *Genome Biology* 27, 111 (2026), https://doi.org/10.1186/s13059-026-04012-2.

The demonstration data are available as MassIVE `MSV000100019` and PRIDE `PXD071206`. Training is available through the [Galaxy Training Network iPepGen learning pathway](https://training.galaxyproject.org/training-material/learning-pathways/neoantigen.html).
