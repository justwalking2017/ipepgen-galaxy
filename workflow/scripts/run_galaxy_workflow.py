from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path

from bioblend.galaxy import GalaxyInstance

from ipepgen.galaxy import execute_workflow, resolve_references


settings = dict(snakemake.params.module)
api_key_env = settings.get("api_key_env", "GALAXY_API_KEY")
api_key = os.getenv(api_key_env)
if not api_key:
    raise RuntimeError(f"Galaxy API key is missing; set environment variable {api_key_env}")

url = settings.get("url", "https://usegalaxy.eu")
workflow_path = Path(snakemake.params.workflow)
output_path = Path(snakemake.output[0])
log_path = Path(snakemake.log[0])
output_path.parent.mkdir(parents=True, exist_ok=True)
log_path.parent.mkdir(parents=True, exist_ok=True)

with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    print(f"Submitting {workflow_path} to {url}", flush=True)
    upstream = [
        json.loads(Path(path).read_text(encoding="utf-8")) for path in snakemake.input
    ]
    inputs = resolve_references(settings.get("inputs", {}), upstream)
    result = execute_workflow(
        GalaxyInstance(url=url, key=api_key),
        workflow_path=workflow_path,
        inputs=inputs,
        history_name=settings.get("history_name", f"iPepGen Snakemake: {workflow_path.stem}"),
        timeout=int(settings.get("timeout", 604800)),
        polling_interval=int(settings.get("polling_interval", 30)),
    )
    result["module"] = snakemake.params.name
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Completed history {result['history_id']}", flush=True)
