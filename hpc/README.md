# Galaxy-free HPC implementation

This workflow executes iPepGen directly with Snakemake and Singularity/Apptainer. It never imports a `.ga` file, contacts a Galaxy server, or uses BioBlend.

## Build containers

```bash
mkdir -p containers
apptainer build containers/ipepgen-genomics.sif hpc/containers/ipepgen-genomics.def
apptainer build containers/ipepgen-helpers.sif hpc/containers/ipepgen-helpers.def
apptainer build containers/ipepgen-proteomics-open.sif hpc/containers/ipepgen-proteomics-open.def
apptainer build containers/ipepgen-hla.sif hpc/containers/ipepgen-hla.def
apptainer build containers/ipepgen-customprodb.sif hpc/containers/ipepgen-customprodb.def
```

FragPipe is not redistributable under the repository's MIT license. Download it under its academic/non-commercial license, place the extracted distribution at `vendor/fragpipe`, and build:

```bash
apptainer build containers/ipepgen-fragpipe-licensed.sif hpc/containers/ipepgen-fragpipe-licensed.def.template
```

The original Galaxy workflow used CustomProDB. The native workflow uses the open-source PrecisionProDB implementation for SAV/InDel protein generation because it accepts explicit local FASTA/GTF/VCF inputs, has a documented CLI, and avoids hidden Galaxy genome-build annotation packages. Its source commit is pinned in the definition file.

## Run on Slurm

```bash
cp hpc/config/config.example.yaml config.yaml
# Edit paths, sample definitions, resources, and licensed components.
snakemake --snakefile hpc/Snakefile --configfile config.yaml \
  --workflow-profile hpc/config/slurm
```

For a scheduler-independent dry run:

```bash
snakemake --snakefile hpc/Snakefile --configfile config.yaml --dry-run --cores 1
```

## Scientific scope

The workflow reproduces the major iPepGen stages natively: fusion/non-reference database generation, FragPipe nonspecific-HLA search, PepQuery2 verification plus BLAST novelty filtering, HLA typing, and MHC-I prioritization. MHCflurry is used as the redistributable local binding predictor; sites with an IEDB/NetMHCpan license can replace the final rule while retaining the same TSV contract.

Exact equivalence to a particular Galaxy history depends on matching its reference snapshots, FragPipe workflow file, and licensed tool versions. PrecisionProDB replaces CustomProDB for native variant translation, so this stage is method-compatible rather than byte-identical to the published Galaxy history. These inputs and deviations are explicit rather than hidden in a Galaxy server.
