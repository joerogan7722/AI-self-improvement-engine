import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def run_tests(
    project_root: Path,
    test_path: Path,
    coverage_report_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Runs pytest tests for the specified path within the project root,
    optionally generating a coverage report.

    Args:
        project_root: The root directory of the project. Pytest will be run from here.
                      Coverage will be measured relative to this root.
        test_path: The path to the tests (file or directory) relative to `project_root`.
                   e.g., Path("tests/unit/test_my_module.py") or Path("tests/").
        coverage_report_dir: Optional path to a directory where the coverage XML report
                             should be saved. If None, no XML report is generated.
                             The report will be named '.coverage.xml' within this directory.

    Returns:
        A dictionary containing:
        - 'success': bool, True if tests passed (return code 0), False otherwise.
        - 'stdout': str, The standard output from the pytest command.
        - 'stderr': str, The standard error from the pytest command.
        - 'coverage_xml_path': Optional[Path], The path to the generated coverage XML report,
                               if requested and successfully created.
    """
    results: Dict[str, Any] = {
        'success': False,
        'stdout': '',
        'stderr': '',
        'coverage_xml_path': None
    }

    # Ensure pytest is available
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        logger.error("Pytest is not installed or not in PATH. Please install it (e.g., pip install pytest pytest-cov).")
        results['stderr'] = "Pytest not found."
        return results
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking pytest version: {e.stderr.decode()}")
        results['stderr'] = f"Error checking pytest version: {e.stderr.decode()}"
        return results

    # Construct the pytest command
    cmd = ["pytest"]

    if coverage_report_dir:
        # Ensure coverage directory exists
        coverage_report_dir.mkdir(parents=True, exist_ok=True)
        coverage_xml_path = coverage_report_dir / ".coverage.xml"

        # Add coverage flags
        # --cov=. will measure coverage for the entire project from project_root
        # --cov-report=xml:path/to/.coverage.xml will save the report
        # --cov-report=term-missing will show missing lines in console
        cmd.extend([
            f"--cov={project_root}",
            f"--cov-report=xml:{coverage_xml_path}",
            "--cov-report=term-missing"
        ])

    cmd.append(str(test_path)) # Add the specific test path or directory

    logger.info(f"Running tests from '{test_path}' with command: {' '.join(cmd)} in directory '{project_root}'")

    try:
        process = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=False)
        results['stdout'] = process.stdout
        results['stderr'] = process.stderr
        results['success'] = process.returncode == 0
        if results['success'] and coverage_report_dir:
            results['coverage_xml_path'] = coverage_xml_path
    except Exception as e:
        logger.exception(f"An unexpected error occurred while running tests for {test_path}: {e}")
        results['stderr'] += f"\nAn unexpected error occurred: {e}"

# AI-generated code improvements:
import xml.etree.ElementTree as ET
        'coverage_xml_path': None,
        'coverage_data': None  # New key to store parsed coverage metrics
            # --- Start: Coverage XML Parsing Logic ---
            if coverage_xml_path.exists():
                try:
                    tree = ET.parse(coverage_xml_path)
                    root = tree.getroot()
                    coverage_data = {
                        'overall': {
                            'line_rate': 0.0,
                            'lines_covered': 0,
                            'lines_valid': 0
                        },
                        'files': []
                    }
                    # Parse overall coverage from <totals> or <coverage> root element
                    totals_element = root.find('totals')
                    source_element = totals_element if totals_element is not None else root
                    coverage_data['overall'] = {
                        'line_rate': float(source_element.get('line-rate', 0.0)),
                        'lines_covered': int(source_element.get('lines-covered', 0)),
                        'lines_valid': int(source_element.get('lines-valid', 0))
                    }
                    # Parse per-file coverage
                    for package_elem in root.findall('packages/package'):
                        for class_elem in package_elem.findall('classes/class'):
                            filename = class_elem.get('filename')
                            if filename:
                                file_line_rate = float(class_elem.get('line-rate', 0.0))
                                file_lines_covered = int(class_elem.get('lines-covered', 0))
                                file_lines_valid = int(class_elem.get('lines-valid', 0))
                                missing_lines = []
                                for line_elem in class_elem.findall('lines/line'):
                                    if line_elem.get('hits') == '0':
                                        try:
                                            missing_lines.append(int(line_elem.get('number')))
                                        except (ValueError, TypeError):
                                            pass
                                coverage_data['files'].append({
                                    'filename': filename,
                                    'line_rate': file_line_rate,
                                    'lines_covered': file_lines_covered,
                                    'lines_valid': file_lines_valid,
                                    'missing_lines': sorted(missing_lines)
                                })
                    results['coverage_data'] = coverage_data
                    logger.info(f"Successfully parsed coverage XML from {coverage_xml_path}")
                except ET.ParseError as pe:
                    logger.warning(f"Failed to parse coverage XML from {coverage_xml_path}: {pe}")
                    results['stderr'] += f"\nFailed to parse coverage XML: {pe}"
                except Exception as parse_e:
                    logger.warning(f"An error occurred while processing coverage XML from {coverage_xml_path}: {parse_e}")
                    results['stderr'] += f"\nError processing coverage XML: {parse_e}"
            # --- End: Coverage XML Parsing Logic ---