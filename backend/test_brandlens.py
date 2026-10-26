import os
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from backend.database import initialize_database
from backend.main import (
    PolicyFactRequest,
    PolicyTermRequest,
    ReviewDecisionRequest,
    ReviewRequest,
    create_policy_fact,
    create_policy_rule,
    policy,
    review_decision,
    review_detail,
    submit_review,
)


class BrandLensWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db_path = os.environ.get("BRANDLENS_DB_PATH")
        os.environ["BRANDLENS_DB_PATH"] = str(Path(self.temp_dir.name) / "brandlens-test.db")
        initialize_database()

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("BRANDLENS_DB_PATH", None)
        else:
            os.environ["BRANDLENS_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_policy_checks_and_human_decision_are_saved(self) -> None:
        self.assertGreaterEqual(len(policy()["rules"]), 1)
        added_rule = create_policy_rule(PolicyTermRequest(term="botanical miracle"))
        create_policy_fact(PolicyFactRequest(text="Delivery takes 3-5 business days"))

        review = submit_review(
            ReviewRequest(
                title="Spring campaign",
                content="Our botanical miracle guarantees results in 3 days.",
            )
        )
        findings = review["findings"]
        self.assertTrue(
            any(item["source_id"] == added_rule["rule_id"] for item in findings)
        )
        self.assertTrue(
            any(item["category"] == "Claim needs verification" for item in findings)
        )
        self.assertIn("botanical miracle", {item["matched_text"] for item in findings})

        decision = review_decision(
            review["id"],
            ReviewDecisionRequest(
                decision="changes_requested",
                note="Please verify the timing claim.",
            ),
        )
        self.assertEqual(decision["status"], "changes_requested")
        self.assertEqual(decision["audit_log"][-1]["action"], "Changes requested")
        self.assertEqual(
            review_detail(review["id"])["reviewer_note"],
            "Please verify the timing claim.",
        )

    def test_exact_approved_fact_supports_a_matching_claim(self) -> None:
        create_policy_fact(PolicyFactRequest(text="Delivery takes 3-5 business days"))
        review = submit_review(
            ReviewRequest(
                title="Delivery information",
                content="Delivery takes 3-5 business days.",
            )
        )
        self.assertEqual(review["total_issues"], 0)

    def test_unrelated_fact_does_not_hide_an_unsupported_claim(self) -> None:
        review = submit_review(
            ReviewRequest(
                title="Mixed evidence",
                content=(
                    "BrandLens provides explainable brand-rule findings, "
                    "and results arrive in 3 days."
                ),
            )
        )
        self.assertTrue(
            any(item["matched_text"] == "3 days" for item in review["findings"])
        )

    def test_blank_draft_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ReviewRequest(content="   ")


if __name__ == "__main__":
    unittest.main()
