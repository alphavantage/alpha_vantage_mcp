from av_cli.main import _apply_limit


# 1. limit=None is a no-op
def test_apply_limit_none_returns_unchanged():
    data = {"Time Series (Daily)": {"2026-03-18": {"1. open": "252.00"}}}
    assert _apply_limit(data, None) is data


# 2. CSV string: header kept, data rows sliced to limit
def test_apply_limit_csv_slices_rows():
    csv = "timestamp,open,high,low,close\n2026-03-18,252,255,249,250\n2026-03-17,251,253,248,249\n2026-03-16,250,252,247,248"
    result = _apply_limit(csv, 2)
    lines = result.splitlines()
    assert lines[0] == "timestamp,open,high,low,close"
    assert len(lines) == 3  # header + 2 data rows


# 3. JSON nested dict: inner time series sliced to limit
def test_apply_limit_nested_dict_slices_entries():
    data = {
        "Meta Data": {"1. Information": "Daily"},
        "Time Series (Daily)": {
            "2026-03-18": {"1. open": "252.00"},
            "2026-03-17": {"1. open": "251.00"},
            "2026-03-16": {"1. open": "250.00"},
        },
    }
    result = _apply_limit(data, 2)
    assert len(result["Time Series (Daily)"]) == 2


# 4. Non-dict, non-string passthrough (e.g. None or list)
def test_apply_limit_passthrough_for_unsupported_types():
    assert _apply_limit(None, 5) is None
    lst = [1, 2, 3]
    assert _apply_limit(lst, 5) is lst


# 5. CLI integration: --limit flag is wired up to the command
def test_limit_flag_exists_on_commands():
    from click.testing import CliRunner
    from av_cli.main import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["TIME_SERIES_DAILY", "--help"])
    assert "--limit" in result.output
    assert "-n" in result.output
