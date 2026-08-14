from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _uploaded_dataset(response: dict[str, Any]) -> dict[str, str]:
    outputs = response.get("outputs", [])
    if not outputs or "id" not in outputs[0]:
        raise RuntimeError(f"Galaxy upload returned no dataset: {response!r}")
    return {"id": outputs[0]["id"], "src": "hda"}


def prepare_inputs(gi: Any, history_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Convert config input declarations to a Galaxy workflow input map."""
    prepared: dict[str, Any] = {}
    for step, declaration in inputs.items():
        if not isinstance(declaration, dict):
            raise ValueError(f"input {step!r} must be an object")
        if "id" in declaration and "src" in declaration:
            prepared[str(step)] = {"id": declaration["id"], "src": declaration["src"]}
            continue
        if "path" in declaration:
            path = Path(declaration["path"]).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(f"input {step!r} does not exist: {path}")
            uploaded = gi.tools.upload_file(
                str(path),
                history_id,
                file_type=declaration.get("file_type", "auto"),
                dbkey=declaration.get("dbkey", "?"),
                to_posix_lines=declaration.get("to_posix_lines", True),
            )
            prepared[str(step)] = _uploaded_dataset(uploaded)
            continue
        raise ValueError(f"input {step!r} requires either id/src or path")
    return prepared


def resolve_references(
    inputs: dict[str, Any], upstream_manifests: list[dict[str, Any]]
) -> dict[str, Any]:
    """Resolve ``from`` declarations against completed upstream manifests."""
    manifests = {item.get("module"): item for item in upstream_manifests}
    resolved: dict[str, Any] = {}
    for step, declaration in inputs.items():
        if not isinstance(declaration, dict) or "from" not in declaration:
            resolved[step] = declaration
            continue
        module = declaration["from"]
        if module not in manifests:
            raise ValueError(f"input {step!r} references unavailable module {module!r}")
        candidates = manifests[module].get("outputs", [])
        if "output_name" in declaration:
            candidates = [item for item in candidates if item.get("name") == declaration["output_name"]]
        elif "output_hid" in declaration:
            candidates = [item for item in candidates if item.get("hid") == declaration["output_hid"]]
        else:
            raise ValueError(
                f"input {step!r} reference requires output_name or output_hid"
            )
        if len(candidates) != 1:
            raise ValueError(
                f"input {step!r} matched {len(candidates)} outputs in module {module!r}"
            )
        resolved[step] = {"id": candidates[0]["id"], "src": candidates[0]["src"]}
    return resolved


def execute_workflow(
    gi: Any,
    workflow_path: Path,
    inputs: dict[str, Any],
    history_name: str,
    timeout: int = 604800,
    polling_interval: int = 30,
) -> dict[str, Any]:
    """Import, invoke, wait for, and summarize a Galaxy workflow execution."""
    history = gi.histories.create_history(name=history_name)
    history_id = history["id"]
    prepared = prepare_inputs(gi, history_id, inputs)
    if any("path" in value for value in inputs.values()):
        gi.histories.wait_for_history(
            history_id, timeout=timeout, polling_interval=polling_interval
        )

    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    imported = gi.workflows.import_workflow_dict(workflow)
    workflow_id = imported["id"]
    invocation = gi.workflows.invoke_workflow(
        workflow_id, inputs=prepared, history_id=history_id
    )
    gi.histories.wait_for_history(
        history_id, timeout=timeout, polling_interval=polling_interval
    )
    contents = gi.histories.show_history(history_id, contents=True, deleted=False)
    failed = [item for item in contents if item.get("state") in {"error", "failed"}]
    if failed:
        names = ", ".join(item.get("name", item.get("id", "unknown")) for item in failed)
        raise RuntimeError(f"Galaxy history contains failed datasets: {names}")
    return {
        "galaxy_url": gi.url.removesuffix("/api"),
        "history_id": history_id,
        "workflow_id": workflow_id,
        "invocation_id": invocation.get("id"),
        "history_name": history_name,
        "inputs": prepared,
        "outputs": [
            {
                "id": item.get("id"),
                "hid": item.get("hid"),
                "name": item.get("name"),
                "state": item.get("state"),
                "src": "hdca" if item.get("history_content_type") == "dataset_collection" else "hda",
            }
            for item in contents
        ],
    }
