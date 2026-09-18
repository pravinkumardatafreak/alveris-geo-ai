"""Unit tests for Phase 11: Production CLI Interface."""

from pathlib import Path

from alveris.cli import create_parser, handle_assess, handle_gates, handle_version


def test_cli_version(capsys):
    """Verify `alveris version` output and exit code."""
    parser = create_parser()
    args = parser.parse_args(["version"])
    ret = handle_version(args)
    assert ret == 0

    captured = capsys.readouterr()
    assert "ALVERIS version" in captured.out
    assert "IPCC AR6 WG1" in captured.out


def test_cli_run_gates(capsys):
    """Verify `alveris run-gates` executes spatial gates on sample parcel."""
    parser = create_parser()
    args = parser.parse_args([
        "run-gates",
        "--parcel", "data/sample/coastal_periurban_parcel.geojson",
    ])
    ret = handle_gates(args)
    assert ret == 0

    captured = capsys.readouterr()
    assert "Gate 1 (CRS Projection): PASSED" in captured.out
    assert "Gate 3 (Coordinate Plausibility): PASSED" in captured.out
    assert "Gate 4 (Metric Area Plausibility" in captured.out


def test_cli_assess_end_to_end(tmp_path: Path, capsys):
    """Verify `alveris assess` runs full pipeline and writes HTML memo."""
    memo_out = tmp_path / "cli_underwriting_memo.html"
    parser = create_parser()
    args = parser.parse_args([
        "assess",
        "--parcel", "data/sample/coastal_periurban_parcel.geojson",
        "--slr", "1.0",
        "--subsidence", "10.0",
        "--horizon", "2050",
        "--output", str(memo_out),
    ])
    ret = handle_assess(args)
    assert ret == 0
    assert memo_out.exists()
    assert memo_out.stat().st_size > 1000

    captured = capsys.readouterr()
    assert "ALVERIS PHYSICAL CLIMATE RISK & UNDERWRITING ASSESSMENT" in captured.out
    assert "Baseline Value:" in captured.out
    assert "Adjusted Value:" in captured.out
    assert "Climate VaR Loss:" in captured.out
    assert "Risk Tier:" in captured.out


def test_cli_missing_parcel_exits_with_error(capsys):
    """Verify CLI handles non-existent parcel path cleanly."""
    parser = create_parser()
    args = parser.parse_args([
        "assess",
        "--parcel", "data/sample/non_existent_file.geojson",
    ])
    ret = handle_assess(args)
    assert ret == 1

    captured = capsys.readouterr()
    assert "Error: Parcel file not found" in captured.err
