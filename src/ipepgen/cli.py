from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKFLOW_DIR = (
    Path.cwd() / "workflows"
    if (Path.cwd() / "workflows").is_dir()
    else PROJECT_ROOT / "workflows"
)
INPUT_TYPES = {"data_input", "data_collection_input", "parameter_input"}


def workflow_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.ga"))


def load_workflow(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("workflow root must be a JSON object")
    return value


def workflow_inputs(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps", {})
    return [step for step in steps.values() if step.get("type") in INPUT_TYPES]


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        workflow = load_workflow(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]
    for key in ("name", "steps"):
        if key not in workflow:
            errors.append(f"missing required key: {key}")
    steps = workflow.get("steps")
    if not isinstance(steps, dict) or not steps:
        errors.append("steps must be a non-empty object")
    return errors


def get_galaxy(url: str, api_key: str):
    try:
        from bioblend.galaxy import GalaxyInstance
    except ImportError as exc:
        raise SystemExit("bioblend is required; install with: pip install -e .") from exc
    return GalaxyInstance(url=url.rstrip("/"), key=api_key)


def command_list(args: argparse.Namespace) -> int:
    for path in workflow_files(args.workflow_dir):
        workflow = load_workflow(path)
        inputs = workflow_inputs(workflow)
        print(f"{path.stem}\t{workflow.get('name', '<unnamed>')}\t{len(inputs)} inputs")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    failed = False
    files = workflow_files(args.workflow_dir)
    if not files:
        print(f"no .ga workflows found in {args.workflow_dir}", file=sys.stderr)
        return 1
    for path in files:
        errors = validate_workflow(path)
        if errors:
            failed = True
            print(f"FAIL {path}: {'; '.join(errors)}")
        else:
            print(f"OK   {path}")
    return int(failed)


def command_import(args: argparse.Namespace) -> int:
    gi = get_galaxy(args.url, args.api_key)
    workflow = load_workflow(args.workflow)
    imported = gi.workflows.import_workflow_dict(workflow)
    print(json.dumps(imported, indent=2))
    return 0


def command_run(args: argparse.Namespace) -> int:
    gi = get_galaxy(args.url, args.api_key)
    mapping = json.loads(args.inputs.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        raise SystemExit("inputs JSON must be an object keyed by workflow input step ID")
    invocation = gi.workflows.invoke_workflow(
        args.workflow_id,
        inputs=mapping,
        history_id=args.history_id,
        history_name=args.history_name,
    )
    print(json.dumps(invocation, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="ipepgen",
        description="Validate, import, and invoke the published iPepGen Galaxy workflows.",
    )
    root.add_argument(
        "--workflow-dir", type=Path, default=DEFAULT_WORKFLOW_DIR,
        help="directory containing .ga workflows (default: %(default)s)",
    )
    sub = root.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="list bundled workflows")
    list_cmd.set_defaults(func=command_list)

    validate_cmd = sub.add_parser("validate", help="validate bundled workflow JSON")
    validate_cmd.set_defaults(func=command_validate)

    import_cmd = sub.add_parser("import", help="import one workflow into a Galaxy account")
    import_cmd.add_argument("workflow", type=Path)
    add_connection_args(import_cmd)
    import_cmd.set_defaults(func=command_import)

    run_cmd = sub.add_parser("run", help="invoke an imported Galaxy workflow")
    run_cmd.add_argument("workflow_id", help="Galaxy workflow ID returned by import")
    run_cmd.add_argument("--inputs", type=Path, required=True, help="JSON input mapping")
    run_cmd.add_argument("--history-id", help="existing Galaxy history ID")
    run_cmd.add_argument("--history-name", default="iPepGen run", help="new history name")
    add_connection_args(run_cmd)
    run_cmd.set_defaults(func=command_run)
    return root


def add_connection_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--url", default=os.getenv("GALAXY_URL", "https://usegalaxy.eu"))
    command.add_argument("--api-key", default=os.getenv("GALAXY_API_KEY"), required=False)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command in {"import", "run"} and not args.api_key:
        raise SystemExit("provide --api-key or set GALAXY_API_KEY")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
