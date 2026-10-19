"""
Automated Test Suite for Academic Assignment Planning AI Agent
==============================================================
Validates:
- Part (c): Workflow checking for missing tasks, conflicting deadlines, and capacity limits.
- Part (d): Scenario 1 (Research Paper) and Scenario 2 (Coding Project) plan generation and dynamic revision.
- Part (e): Safety evaluation, DAG dependency integrity, and buffer compliance.
"""

import unittest
from datetime import date, timedelta
from academic_planner_app import (
    AcademicPlanner,
    PlanValidator,
    PlanReviser,
    AssignmentInput,
    DeliverableType,
    Priority,
    TaskItem
)


class TestAcademicPlannerAgent(unittest.TestCase):

    def setUp(self):
        self.planner = AcademicPlanner()
        self.validator = PlanValidator()
        self.reviser = PlanReviser()

    def test_scenario_1_research_paper(self):
        """Test Scenario 1: Capstone Research Paper (BIO-702)"""
        assignment = AssignmentInput(
            assignment_id="SCENARIO_1",
            title="Ethical & Regulatory Implications of Healthcare LLMs",
            course="BIO-702 / AI Ethics",
            description="3,500-word comprehensive literature review, 15 peer-reviewed papers, APA 7th format.",
            deliverable_type=DeliverableType.RESEARCH_PAPER,
            start_date=date(2026, 10, 20),
            due_date=date(2026, 11, 3),  # 14 days
            daily_capacity_hours=2.5,
            difficulty_multiplier=1.0
        )

        plan = self.planner.generate_plan(assignment)
        report = self.validator.validate(plan, assignment)

        # Assertions
        self.assertTrue(report.is_valid, f"Scenario 1 plan validation failed: {report.errors}")
        self.assertEqual(len(report.missing_tasks), 0, "Missing mandatory academic phases detected.")
        self.assertEqual(len(report.conflicting_deadlines), 0, "Conflicting deadlines found.")
        self.assertEqual(len(report.capacity_violations), 0, "Daily capacity was exceeded.")
        self.assertGreaterEqual(len(plan), 5, "Expected at least 5 decomposed tasks.")

    def test_scenario_2_coding_project(self):
        """Test Scenario 2: Technical ML Coding Project (CS-640)"""
        assignment = AssignmentInput(
            assignment_id="SCENARIO_2",
            title="Distributed Inference Pipeline with vLLM & Redis",
            course="CS-640: Distributed Systems for AI",
            description="Implement an asynchronous task queue with model shard workers, load tests, and PDF report.",
            deliverable_type=DeliverableType.CODING_PROJECT,
            start_date=date(2026, 10, 20),
            due_date=date(2026, 10, 30),  # 10 days
            daily_capacity_hours=3.0,
            difficulty_multiplier=1.0
        )

        plan = self.planner.generate_plan(assignment)
        report = self.validator.validate(plan, assignment)

        # Assertions
        self.assertTrue(report.is_valid, f"Scenario 2 plan validation failed: {report.errors}")
        self.assertEqual(len(report.missing_tasks), 0)
        self.assertEqual(len(report.conflicting_deadlines), 0)
        self.assertEqual(len(report.capacity_violations), 0)

    def test_dynamic_re-planning_on_deadline_compression(self):
        """Test dynamic plan revision when requirement shifts (deadline advanced by 4 days)."""
        assignment = AssignmentInput(
            assignment_id="SCENARIO_1",
            title="Ethical & Regulatory Implications of Healthcare LLMs",
            course="BIO-702 / AI Ethics",
            description="3,500-word comprehensive literature review.",
            deliverable_type=DeliverableType.RESEARCH_PAPER,
            start_date=date(2026, 10, 20),
            due_date=date(2026, 11, 3),
            daily_capacity_hours=2.5
        )

        original_plan = self.planner.generate_plan(assignment)
        new_due_date = date(2026, 10, 30)  # Shortened by 4 days

        revised_plan, rev_report = self.reviser.revise_plan(
            original_tasks=original_plan,
            assignment=assignment,
            new_due_date=new_due_date,
            reason="Instructor advanced deadline by 4 days"
        )

        # Assertions
        self.assertTrue(rev_report.is_valid, f"Revised plan validation failed: {rev_report.errors}")
        for t in revised_plan:
            self.assertLessEqual(t.deadline, new_due_date, f"Task {t.task_id} exceeds revised due date!")

    def test_validator_catches_missing_phase(self):
        """Ensure the validator correctly flags missing mandatory academic tasks."""
        assignment = AssignmentInput(
            assignment_id="TEST_MISSING",
            title="Incomplete Paper",
            course="ENG-101",
            description="Sample",
            deliverable_type=DeliverableType.RESEARCH_PAPER,
            start_date=date(2026, 10, 20),
            due_date=date(2026, 10, 28),
            daily_capacity_hours=3.0
        )

        # Intentionally create tasks omitting "research" and "revision"
        flawed_tasks = [
            TaskItem(
                task_id="T01",
                phase="Drafting",
                title="Only drafting without research or outline",
                priority=Priority.HIGH,
                estimated_hours=2.0,
                scheduled_date=date(2026, 10, 21),
                deadline=date(2026, 10, 21),
                definition_of_done="Draft written."
            )
        ]

        report = self.validator.validate(flawed_tasks, assignment)
        self.assertFalse(report.is_valid, "Validator should have rejected plan with missing phases.")
        self.assertTrue(any("RESEARCH" in m for m in report.missing_tasks))
        self.assertTrue(any("REVISION" in m for m in report.missing_tasks))

    def test_validator_catches_dependency_inversion(self):
        """Ensure the validator flags when a dependent task is scheduled before its prerequisite."""
        assignment = AssignmentInput(
            assignment_id="TEST_INVERSION",
            title="Inverted Paper",
            course="ENG-101",
            description="Sample",
            deliverable_type=DeliverableType.RESEARCH_PAPER,
            start_date=date(2026, 10, 20),
            due_date=date(2026, 10, 28),
            daily_capacity_hours=3.0
        )

        inverted_tasks = [
            TaskItem(
                task_id="T01",
                phase="Research",
                title="Literature Research",
                priority=Priority.HIGH,
                estimated_hours=2.0,
                scheduled_date=date(2026, 10, 23),
                deadline=date(2026, 10, 23),
                dependencies=[],
                definition_of_done="Papers read."
            ),
            TaskItem(
                task_id="T02",
                phase="Drafting",
                title="Drafting based on Research",
                priority=Priority.HIGH,
                estimated_hours=2.0,
                scheduled_date=date(2026, 10, 21),  # Starts BEFORE T01 finishes!
                deadline=date(2026, 10, 21),
                dependencies=["T01"],
                definition_of_done="Draft completed."
            )
        ]

        report = self.validator.validate(inverted_tasks, assignment)
        self.assertFalse(report.is_valid, "Validator should have flagged dependency inversion.")
        self.assertTrue(any("Dependency inversion" in err for err in report.conflicting_deadlines))


if __name__ == "__main__":
    unittest.main()
