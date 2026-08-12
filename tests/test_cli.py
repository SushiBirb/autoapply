from click.testing import CliRunner
from autoapply.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "autoapply" in result.output


def test_cli_doctor():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "Doctor" in result.output
    assert "Python" in result.output


def test_cli_log_and_list(tmp_data_dir):
    runner = CliRunner()
    log_res = runner.invoke(main, [
        "log",
        "--company", "Mandiant",
        "--title", "SOC Intern",
        "--platform", "linkedin_easyapply",
        "--status", "submitted",
    ])
    assert log_res.exit_code == 0
    assert "Logged #1: Mandiant" in log_res.output

    list_res = runner.invoke(main, ["list"])
    assert list_res.exit_code == 0
    assert "Mandiant" in list_res.output
    assert "SOC Intern" in list_res.output


def test_cli_stats(tmp_data_dir):
    runner = CliRunner()
    runner.invoke(main, ["log", "--company", "Tenable", "--title", "Security Intern"])
    stats_res = runner.invoke(main, ["stats"])
    assert stats_res.exit_code == 0
    assert "Total applied: 1" in stats_res.output


def test_cli_login(monkeypatch):
    from unittest.mock import MagicMock
    mock_ctx = MagicMock()
    mock_page = MagicMock()
    monkeypatch.setattr("autoapply.browser.launch_browser_session", lambda headless=False: MagicMock(__enter__=lambda s: (mock_ctx, mock_page), __exit__=lambda s, a, b, c: None))
    
    runner = CliRunner()
    res = runner.invoke(main, ["login"], input="\n")
    assert res.exit_code == 0
    assert "Session state saved" in res.output
