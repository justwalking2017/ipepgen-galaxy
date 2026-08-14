from pathlib import Path

import pytest

from ipepgen.galaxy import execute_workflow, prepare_inputs, resolve_references


class Tools:
    def upload_file(self, path, history_id, **kwargs):
        return {"outputs": [{"id": "uploaded-id"}]}


class Histories:
    def __init__(self):
        self.waits = 0

    def create_history(self, name):
        return {"id": "history-id", "name": name}

    def wait_for_history(self, history_id, **kwargs):
        self.waits += 1

    def show_history(self, history_id, **kwargs):
        return [{"id": "output-id", "hid": 2, "name": "result", "state": "ok", "history_content_type": "dataset"}]


class Workflows:
    def import_workflow_dict(self, workflow):
        return {"id": "workflow-id"}

    def invoke_workflow(self, workflow_id, **kwargs):
        return {"id": "invocation-id"}


class Galaxy:
    url = "https://example.org/api"
    tools = Tools()
    histories = Histories()
    workflows = Workflows()


def test_prepare_existing_dataset():
    result = prepare_inputs(Galaxy(), "history", {"0": {"id": "abc", "src": "hda"}})
    assert result == {"0": {"id": "abc", "src": "hda"}}


def test_prepare_upload(tmp_path: Path):
    source = tmp_path / "input.txt"
    source.write_text("test", encoding="utf-8")
    result = prepare_inputs(Galaxy(), "history", {"4": {"path": str(source)}})
    assert result["4"] == {"id": "uploaded-id", "src": "hda"}


def test_execute_workflow(tmp_path: Path):
    workflow = tmp_path / "workflow.ga"
    workflow.write_text('{"name": "test", "steps": {"0": {}}}', encoding="utf-8")
    result = execute_workflow(
        Galaxy(), workflow, {"0": {"id": "abc", "src": "hda"}}, "test history"
    )
    assert result["invocation_id"] == "invocation-id"
    assert result["outputs"][0]["id"] == "output-id"


def test_rejects_invalid_input():
    with pytest.raises(ValueError):
        prepare_inputs(Galaxy(), "history", {"0": {"unexpected": True}})


def test_resolve_upstream_reference():
    manifests = [{
        "module": "gene_fusion",
        "outputs": [{"id": "fusion-id", "hid": 21, "name": "Fusion FASTA", "src": "hda"}],
    }]
    resolved = resolve_references(
        {"0": {"from": "gene_fusion", "output_name": "Fusion FASTA"}}, manifests
    )
    assert resolved == {"0": {"id": "fusion-id", "src": "hda"}}
