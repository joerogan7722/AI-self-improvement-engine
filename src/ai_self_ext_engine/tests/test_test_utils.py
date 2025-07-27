import pytest
from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess
from unittest.mock import patch, MagicMock

# Import the function under test using a relative import
# This assumes the test file is located in src/ai_self_ext_engine/tests/
# and the module under test is in src/ai_self_ext_engine/
from ..test_utils import run_tests

@pytest.fixture
def temp_project(tmp_path: Path):
    """
    A pytest fixture to create a temporary project structure for testing `run_tests`.
    It sets up a project root, a source directory with a module, and a tests directory
    with passing and failing tests.
    """
    project_root = tmp_path / "my_test_project"
    project_root.mkdir()

    # Create a dummy source directory structure that pytest-cov can track
    src_dir = project_root / "src"
    src_dir.mkdir()
    engine_dir = src_dir / "ai_self_ext_engine"
    engine_dir.mkdir()
    # Ensure __init__.py exists for importability
    (engine_dir / "__init__.py").write_text("")
    (engine_dir / "my_module.py").write_text(
        "def my_func_covered(): return True\n"
        "def my_func_uncovered(): return False"
    )

    # Create a tests directory
    tests_dir = project_root / "tests"
    tests_dir.mkdir()
    # Create a subdirectory for unit tests
    unit_tests_dir = tests_dir / "unit"
    unit_tests_dir.mkdir()

    # Create a passing test file that covers one function
    (unit_tests_dir / "test_passing.py").write_text(
        """
import pytest
from src.ai_self_ext_engine.my_module import my_func_covered

def test_my_func_covered_passes():
    assert my_func_covered() is True
"""
    )

    # Create a failing test file
    (unit_tests_dir / "test_failing.py").write_text(
        """
import pytest

def test_always_fails():
    assert False
"""
    )

    # Create another passing test file, to test running multiple or directory
    (unit_tests_dir / "test_another_passing.py").write_text(
        """
import pytest

def test_simple_passing():
    assert 1 == 1
"""
    )

    # Create a file that is not a test
    (project_root / "non_test_file.txt").write_text("This is not a test file.")

    return project_root


def test_run_tests_success_single_file(temp_project: Path):
    """Verify running a single passing test file reports success."""
    test_file_path = Path("tests/unit/test_passing.py")
    results = run_tests(project_root=temp_project, test_path=test_file_path)

    assert results['success'] is True
    assert "1 passed" in results['stdout']
    assert "0 failed" in results['stdout']
    assert results['stderr'] == ""
    assert results['coverage_xml_path'] is None


def test_run_tests_failure_single_file(temp_project: Path):
    """Verify running a single failing test file reports failure."""
    test_file_path = Path("tests/unit/test_failing.py")
    results = run_tests(project_root=temp_project, test_path=test_file_path)

    assert results['success'] is False
    assert "1 failed" in results['stdout']
    assert "0 passed" in results['stdout']
    assert "test_always_fails" in results['stdout']
    assert results['stderr'] == ""
    assert results['coverage_xml_path'] is None


def test_run_tests_directory_mixed_results(temp_project: Path):
    """Verify running tests in a directory with mixed results (pass/fail)."""
    test_dir_path = Path("tests/unit")
    results = run_tests(project_root=temp_project, test_path=test_dir_path)

    # There are 2 passing tests and 1 failing test
    assert results['success'] is False  # Because one test fails
    assert "2 passed" in results['stdout']
    assert "1 failed" in results['stdout']
    assert "test_always_fails" in results['stdout']
    assert results['stderr'] == ""
    assert results['coverage_xml_path'] is None


def test_run_tests_non_existent_path(temp_project: Path):
    """Verify behavior when the specified test_path does not exist."""
    non_existent_path = Path("tests/non_existent/file.py")
    results = run_tests(project_root=temp_project, test_path=non_existent_path)

    assert results['success'] is False
    # Pytest typically reports "collected 0 items" for non-existent paths, sometimes with exit code 5
    assert "No tests ran" in results['stdout'] or "collected 0 items" in results['stdout']
    assert results['stderr'] == ""


def test_run_tests_with_coverage(temp_project: Path, tmp_path: Path):
    """Verify that coverage reports are generated correctly when requested."""
    coverage_report_dir = tmp_path / "coverage_reports"
    test_file_path = Path("tests/unit/test_passing.py")

    results = run_tests(
        project_root=temp_project,
        test_path=test_file_path,
        coverage_report_dir=coverage_report_dir
    )

    assert results['success'] is True
    assert results['coverage_xml_path'] is not None
    assert results['coverage_xml_path'].exists()
    assert results['coverage_xml_path'].parent == coverage_report_dir
    assert results['coverage_xml_path'].name == ".coverage.xml"
    assert "1 passed" in results['stdout']
    assert "coverage" in results['stdout'].lower()  # Should see coverage output in term-missing

    # Verify content of the XML report
    tree = ET.parse(results['coverage_xml_path'])
    root = tree.getroot()
    # Check for the package and file
    package_element = root.find(".//package[@name='src.ai_self_ext_engine']")
    assert package_element is not None, "Package 'src.ai_self_ext_engine' not found in coverage XML."
    file_element = package_element.find(".//file[@name='my_module.py']")
    assert file_element is not None, "File 'my_module.py' not found in coverage XML."
    
    # my_module.py has two functions, my_func_covered and my_func_uncovered.
    # test_passing.py only calls my_func_covered. So expect 1 line covered out of 2 statements.
    lines_covered = sum(1 for line in file_element.findall(".//line") if line.get('hits') == '1')
    assert lines_covered == 1, f"Expected 1 covered line in my_module.py, but found {lines_covered}"
    
    # Also check total statements and misses
    lines = file_element.findall(".//line")
    assert len(lines) == 2, f"Expected 2 lines in my_module.py, but found {len(lines)}"
    assert sum(1 for line in lines if line.get('hits') == '0') == 1, "Expected 1 missed line"


def test_run_tests_with_coverage_directory_creation(temp_project: Path, tmp_path: Path):
    """Verify that the coverage report directory is created if it does not exist."""
    non_existent_coverage_dir = tmp_path / "non_existent_coverage_dir" / "subdir"
    test_file_path = Path("tests/unit/test_passing.py")

    results = run_tests(
        project_root=temp_project,
        test_path=test_file_path,
        coverage_report_dir=non_existent_coverage_dir
    )

    assert results['success'] is True
    assert non_existent_coverage_dir.exists()
    assert results['coverage_xml_path'] is not None
    assert results['coverage_xml_path'].parent == non_existent_coverage_dir


@patch('subprocess.run')
def test_run_tests_pytest_not_found(mock_subprocess_run: MagicMock, temp_project: Path):
    """Verify error handling when pytest executable is not found."""
    # Simulate FileNotFoundError when checking pytest version
    mock_subprocess_run.side_effect = FileNotFoundError

    results = run_tests(project_root=temp_project, test_path=Path("tests/unit/test_passing.py"))
