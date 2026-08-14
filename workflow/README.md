# Snakemake orchestration

The Snakefile offers two execution modes:

- `one-click`: submits the official end-to-end Galaxy workflow as one Snakemake job.
- `modular`: represents the seven published modules as a DAG. Gene-fusion and general non-reference database generation run in parallel; HLA genotyping is also independent until peptide–HLA binding prediction.

Galaxy performs the scientific computation. Snakemake manages dependencies, remote submission, polling, failure propagation, logs, and result manifests.

```bash
pip install -e ".[workflow]"
cp workflow/config/config.example.yaml config.yaml
# Edit config.yaml and provide real step input mappings.
export GALAXY_API_KEY=your-key
snakemake --snakefile workflow/Snakefile --configfile config.yaml --cores 2
```

Preview the DAG without submitting anything:

```bash
snakemake --snakefile workflow/Snakefile --configfile config.yaml --dry-run --cores 2
```

Each successful rule writes a JSON manifest containing the Galaxy workflow, invocation, history, resolved inputs, and every history output. Logs are written below `results/logs/`.

In modular mode, downstream inputs can be wired to upstream outputs without knowing Galaxy IDs in advance:

```yaml
discovery:
  inputs:
    "0": {from: gene_fusion, output_name: "Fusion FASTA"}
    "1": {from: non_reference, output_hid: 41}
```

`output_name` must match exactly one history item; `output_hid` selects by Galaxy history item number. The resolved dataset or collection ID is recorded in the downstream manifest.
