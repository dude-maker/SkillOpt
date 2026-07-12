import os
import tempfile
import unittest
from pathlib import Path

from skillopt_sleep.plan import validate_plan


class PlanValidatorTests(unittest.TestCase):
    def test_plan_validator_finds_next_action(self):
        root = os.environ.get("IMPLEMENTATION_PLANS_ROOT", "/home/user/projects/implementation-plans")
        path = Path(root) / "plans/comfyui-newsroom-automation.html"
        if not path.exists():
            self.skipTest("implementation-plans checkout is not available")
        result = validate_plan(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["next_section"], "install-dgx-runtime-broker")

    def test_plan_validator_rejects_missing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.html"
            plan.write_text(
                "<main data-plan-id='p' data-timezone='America/New_York' data-human-path='/human/plans' "
                "data-codex-path='/codex/plans' data-opencode-path='/workspace/plans' data-remote-url='https://example.test/plans.git' data-status='in_progress' "
                "data-updated-at='2026-07-12T06:00:00-04:00'>"
                "<section data-section-id='a' data-status='complete' data-updated-at='2026-07-12T06:00:00-04:00' "
                "data-started-at='2026-07-12T05:00:00-04:00' data-completed-at='2026-07-12T06:00:00-04:00' data-test='pytest' "
                "data-acceptance='works'></section></main>",
                encoding="utf-8",
            )
            result = validate_plan(plan)
        self.assertFalse(result["valid"])
        self.assertIn("a: missing data-evidence", result["errors"])


if __name__ == "__main__":
    unittest.main()
