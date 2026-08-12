"""CI가 실패를 숨기거나 중복 실행으로 다시 갈라지는 것을 막는 계약 테스트."""

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPOSITORY_ROOT / ".github" / "workflows"
CI_WORKFLOW = WORKFLOW_DIR / "ci.yml"


def test_ci_uses_one_canonical_blocking_workflow():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert not (WORKFLOW_DIR / "coverage-boost.yml").exists()

    required_blocking_commands = (
        "ruff check kis_agent",
        "black --check kis_agent",
        "bandit -q -r kis_agent -x tests -s B413 -lll",
        "fake_data_detector.py kis_agent --ci",
        "pytest tests",
        '--cov-fail-under="${COVERAGE_MINIMUM}"',
    )
    for command in required_blocking_commands:
        assert command in workflow


def test_all_workflows_fail_closed_and_pin_actions_to_commit_shas():
    workflows = list(WORKFLOW_DIR.glob("*.yml"))
    assert workflows

    for path in workflows:
        workflow = path.read_text(encoding="utf-8")
        assert "continue-on-error: true" not in workflow
        assert "|| true" not in workflow
        assert "2>&1 | tee" not in workflow
        assert "@main" not in workflow

        action_revisions = re.findall(
            r"^\s*uses:\s+[^\s@]+@([^\s#]+)", workflow, re.MULTILINE
        )
        assert all(
            re.fullmatch(r"[0-9a-f]{40}", revision) for revision in action_revisions
        )

    assert "mkdocs build --strict" in (WORKFLOW_DIR / "docs.yml").read_text(
        encoding="utf-8"
    )
    ci_workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r'CI_HELPERS_REVISION: "[0-9a-f]{40}"', ci_workflow)
