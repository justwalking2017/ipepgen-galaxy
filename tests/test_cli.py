import json
from pathlib import Path

from ipepgen.cli import DEFAULT_WORKFLOW_DIR, load_workflow, validate_workflow, workflow_files, workflow_inputs


def test_all_bundled_workflows_are_valid():
    files = workflow_files(DEFAULT_WORKFLOW_DIR)
    assert len(files) == 8
    for path in files:
        assert validate_workflow(path) == []


def test_one_click_has_inputs():
    workflow = load_workflow(DEFAULT_WORKFLOW_DIR / "one-click.ga")
    assert workflow["name"].startswith("OneClick-iPepGen")
    assert len(workflow_inputs(workflow)) >= 1


def test_invalid_workflow(tmp_path: Path):
    path = tmp_path / "broken.ga"
    path.write_text(json.dumps({"name": "broken", "steps": {}}), encoding="utf-8")
    assert validate_workflow(path)

