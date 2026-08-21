import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
DATA = ROOT / "scneo" / "tests" / "data"
SCRIPTS = ROOT / "scneo" / "scripts"


def run(script, *args):
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True, cwd=ROOT)


def rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_excludes_annotated_and_normal_supported_junctions(tmp_path):
    output = tmp_path / "junctions.tsv"
    run("filter_junctions.py", DATA / "junction_counts.tsv", DATA / "cell_metadata.tsv", output,
        "--annotated", DATA / "annotated.txt", "--min-tumor-cells", "2", "--min-tumor-reads", "3")
    result = rows(output)
    assert [row["junction_id"] for row in result] == ["chr1:31-61:+"]
    assert result[0]["tumor_cells"] == "3"


def test_translation_self_filter_and_mock_prediction(tmp_path):
    junctions = tmp_path / "junctions.tsv"
    peptides = tmp_path / "peptides.tsv"
    fasta = tmp_path / "peptides.fa"
    novel = tmp_path / "novel.tsv"
    predicted = tmp_path / "predicted.tsv"
    run("filter_junctions.py", DATA / "junction_counts.tsv", DATA / "cell_metadata.tsv", junctions,
        "--annotated", DATA / "annotated.txt", "--min-tumor-cells", "2", "--min-tumor-reads", "3")
    run("translate_junctions.py", junctions, DATA / "genome.fa", peptides, fasta, "--flank-nt", "30", "--lengths", "8,9")
    run("filter_self.py", peptides, DATA / "proteome.fa", novel)
    run("predict_mhc.py", novel, DATA / "hla.txt", predicted, "--backend", "mock", "--max-affinity", "5000")
    result = rows(predicted)
    assert result
    assert all(row["prediction_backend"] == "mock" for row in result)
    assert all(row["reference_match"] == "no" for row in result)
    assert all(int(row["length"]) in {8, 9} for row in result)


def test_scasl_matrix_conversion(tmp_path):
    matrix = tmp_path / "junc_matrix.csv"
    matrix.write_text("junction_id,T1,T2,N1\nchr1:31-61:+,3,2,0\n", encoding="utf-8")
    output = tmp_path / "long.tsv"
    run("scasl_matrix_to_long.py", matrix, output)
    assert rows(output) == [
        {"junction_id": "chr1:31-61:+", "cell_id": "T1", "count": "3"},
        {"junction_id": "chr1:31-61:+", "cell_id": "T2", "count": "2"},
    ]


def test_consensus_and_html_report(tmp_path):
    primary = tmp_path / "primary.tsv"
    snaf = tmp_path / "snaf.tsv"
    pvac = tmp_path / "pvac.tsv"
    consensus = tmp_path / "consensus.tsv"
    report = tmp_path / "report.html"
    primary.write_text("candidate_id\tjunction_id\tpeptide\tbest_allele\taffinity_nm\tpresentation_score\ttumor_cells\ttumor_reads\nC1\tchr1:31-61:+\tAAAAAAAA\tHLA-A*02:01\t100\t0.9\t3\t6\n", encoding="utf-8")
    snaf.write_text("method\tstatus\tjunction_id\tpeptide\tallele\taffinity_nm\tsource_file\nsnaf\tcandidate\tJ1\tAAAAAAAA\tHLA-A*02:01\t90\tx\n", encoding="utf-8")
    pvac.write_text("method\tstatus\tjunction_id\tpeptide\tallele\taffinity_nm\tsource_file\npvacsplice\tnot_run: no VCF\t\t\t\t\t\n", encoding="utf-8")
    run("consensus.py", primary, snaf, pvac, consensus)
    assert rows(consensus)[0]["cross_validated"] == "yes"
    run("render_report.py", consensus, DATA / "junction_counts.tsv", snaf, pvac, report,
        "--metadata-json", DATA / "report.json")
    rendered = report.read_text(encoding="utf-8")
    assert "iPepGen scNeo candidate report" in rendered
    assert "AAAAAAAA" in rendered
