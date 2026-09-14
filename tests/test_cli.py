import subprocess


def test_installed_command_reports_its_version() -> None:
    from importlib.metadata import version

    result = subprocess.run(
        ["dev-assistant", "--version"], check=True, capture_output=True, text=True
    )
    assert result.stdout.strip() == f"dev-assistant {version('dev-assistant')}"
