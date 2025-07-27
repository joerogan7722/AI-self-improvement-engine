import pytest
from typer.testing import CliRunner
from pathlib import Path
from unittest.mock import MagicMock

# Import the Typer app from cli.py
from src.ai_self_ext_engine.cli import app

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_run_tests_with_coverage(mocker):
    """Fixture to mock run_tests_with_coverage for testing purposes."""
    mock = mocker.patch("src.ai_self_ext_engine.cli.run_tests_with_coverage")
    mock.return_value = {
        "success": True,
        "stdout": "Mock tests ran successfully.",
        "stderr": "",
        "coverage_xml_path": Path("mock_coverage.xml"),
        "coverage_data": {"statements": "90%", "branches": "80%"}
    }
    return mock

# Test cases for the 'test' command

def test_run_tests_command_success_explicit_dir(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests successful execution with an explicitly provided test directory."""
    test_dir = tmp_path / "my_tests"
    test_dir.mkdir()
    (test_dir / "test_dummy.py").touch()

    # Create dummy project root and coverage dir within tmp_path to keep things clean
    project_root = tmp_path / "project_root_dummy"
    project_root.mkdir()
    coverage_report_dir = tmp_path / "coverage_reports_custom"

    result = runner.invoke(app, [
        "test",
        str(test_dir),
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    assert "Tests completed successfully." in result.stdout
    assert "Code coverage report generated" in result.stdout
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=test_dir,
        coverage_report_dir=coverage_report_dir
    )
    assert coverage_report_dir.is_dir() # Verify directory creation

def test_run_tests_command_success_explicit_file(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests successful execution with an explicitly provided test file."""
    test_file = tmp_path / "test_single.py"
    test_file.touch()

    project_root = tmp_path / "project_root_dummy"
    project_root.mkdir()
    coverage_report_dir = tmp_path / "coverage_reports_custom"

    result = runner.invoke(app, [
        "test",
        str(test_file),
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    assert "Tests completed successfully." in result.stdout
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=test_file,
        coverage_report_dir=coverage_report_dir
    )

def test_run_tests_command_infer_path_project_root_tests(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests inferring test path from <project_root>/tests/ (highest precedence)."""
    project_root = tmp_path / "my_project"
    # Only create the highest precedence path
    (project_root / "tests").mkdir(parents=True)
    (project_root / "tests" / "test_foo.py").touch()

    coverage_report_dir = tmp_path / "coverage_reports_output"

    result = runner.invoke(app, [
        "test",
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    assert "Running tests from" in result.stdout
    assert str(project_root / "tests") in result.stdout # Ensure the correct path was chosen
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=(project_root / "tests"),
        coverage_report_dir=coverage_report_dir
    )

def test_run_tests_command_infer_path_src_ai_self_ext_engine_tests(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests inferring test path from <project_root>/src/ai_self_ext_engine/tests/ (second precedence)."""
    project_root = tmp_path / "my_project"
    # Ensure higher precedence paths don't exist
    # (project_root / "tests") should not exist
    (project_root / "src" / "ai_self_ext_engine" / "tests").mkdir(parents=True)
    (project_root / "src" / "ai_self_ext_engine" / "tests" / "test_bar.py").touch()

    coverage_report_dir = tmp_path / "coverage_reports_output"

    result = runner.invoke(app, [
        "test",
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    assert str(project_root / "src" / "ai_self_ext_engine" / "tests") in result.stdout
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=(project_root / "src" / "ai_self_ext_engine" / "tests"),
        coverage_report_dir=coverage_report_dir
    )

def test_run_tests_command_infer_path_src_tests(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests inferring test path from <project_root>/src/tests/ (lowest precedence)."""
    project_root = tmp_path / "my_project"
    # Ensure higher precedence paths don't exist
    # (project_root / "tests") should not exist
    # (project_root / "src" / "ai_self_ext_engine" / "tests") should not exist
    (project_root / "src" / "tests").mkdir(parents=True)
    (project_root / "src" / "tests" / "test_baz.py").touch()

    coverage_report_dir = tmp_path / "coverage_reports_output"

    result = runner.invoke(app, [
        "test",
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    assert str(project_root / "src" / "tests") in result.stdout
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=(project_root / "src" / "tests"),
        coverage_report_dir=coverage_report_dir
    )

def test_run_tests_command_infer_path_precedence(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests that test path inference follows the specified precedence when multiple exist."""
    project_root = tmp_path / "my_project"
    # Create all possible paths, ensure the first one is picked
    (project_root / "tests").mkdir(parents=True) # This should be picked
    (project_root / "src" / "ai_self_ext_engine" / "tests").mkdir(parents=True)
    (project_root / "src" / "tests").mkdir(parents=True)
    (project_root / "tests" / "test_priority.py").touch()

    coverage_report_dir = tmp_path / "coverage_reports_output"

    result = runner.invoke(app, [
        "test",
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 0
    # The 'tests' directory directly under project_root should be chosen
    assert str(project_root / "tests") in result.stdout
    mock_run_tests_with_coverage.assert_called_once_with(
        project_root=project_root,
        test_path=(project_root / "tests"),
        coverage_report_dir=coverage_report_dir
    )

def test_run_tests_command_no_tests_path_found(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests exiting with error when no test path is provided and none found."""
    project_root = tmp_path / "empty_project"
    project_root.mkdir() # No 'tests' or 'src/tests' inside

    result = runner.invoke(app, ["test", "--project-root", str(project_root)])

    assert result.exit_code == 1
    assert "No specific tests path provided and no 'tests' directory found" in result.stderr
    mock_run_tests_with_coverage.assert_not_called()

def test_run_tests_command_failure_scenario(runner, mock_run_tests_with_coverage, tmp_path):
    """Tests command behavior when run_tests_with_coverage reports failure."""
    mock_run_tests_with_coverage.return_value = {
        "success": False,
        "stdout": "Some tests failed.",
        "stderr": "Error: Assertions failed.",
        "coverage_xml_path": None,
        "coverage_data": None
    }

    test_dir = tmp_path / "my_tests"
    test_dir.mkdir()
    (test_dir / "test_dummy.py").touch()
    project_root = tmp_path / "project_root_dummy"
    project_root.mkdir()
    coverage_report_dir = tmp_path / "coverage_reports_custom"

    result = runner.invoke(app, [
        "test",
        str(test_dir),
        "--project-root", str(project_root),
        "--coverage-report-dir", str(coverage_report_dir)
    ])

    assert result.exit_code == 1
    assert "Tests failed!" in result.stderr
    assert "Stdout:\nSome tests failed." in result.stderr
    assert "Stderr:\nError: Assertions failed." in result.stderr
    mock_run_tests_with_coverage.assert_called_once()
    assert coverage_report_dir.is_dir() # Should still create the dir even on test failure

def test_run_tests_command_default_options(runner, mock_run_tests_with_coverage, tmp_path, monkeypatch):
    """Tests command behavior with default project_root and coverage_report_dir."""
    # Setup a temporary CWD and put a 'tests' directory inside it.
