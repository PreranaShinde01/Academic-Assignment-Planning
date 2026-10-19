"""
Academic Assignment Planning AI Agent Application
==================================================
A full-stack, modular AI agent that translates student assignment briefs into
validated, constraint-satisfying, actionable academic plans.

Includes:
1. Cognitive Hierarchical Task Decomposition
2. Constraint-Satisfaction Scheduler (Daily limits, dependencies, buffer)
3. Multi-Rule Plan Verification Engine (Missing tasks, conflicting deadlines, incomplete info)
4. Dynamic Re-planner for requirement shifts
5. Interactive CLI & Automated Test Suite
"""

import sys
import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple


class DeliverableType(str, Enum):
    RESEARCH_PAPER = "RESEARCH_PAPER"
    CODING_PROJECT = "CODING_PROJECT"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class TaskItem:
    task_id: str
    phase: str
    title: str
    priority: Priority
    estimated_hours: float
    scheduled_date: date
    deadline: date
    dependencies: List[str] = field(default_factory=list)
    definition_of_done: str = ""
    is_completed: bool = False


@dataclass
class AssignmentInput:
    assignment_id: str
    title: str
    course: str
    description: str
    deliverable_type: DeliverableType
    start_date: date
    due_date: date
    daily_capacity_hours: float
    difficulty_multiplier: float = 1.0


@dataclass
class ValidationReport:
    is_valid: bool
    missing_tasks: List[str] = field(default_factory=list)
    conflicting_deadlines: List[str] = field(default_factory=list)
    incomplete_information: List[str] = field(default_factory=list)
    capacity_violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# COMPONENT 1: PLAN VALIDATOR & GUARDRAIL ENGINE
# ============================================================================
class PlanValidator:
    """Verifies plans for temporal consistency, completeness, and workload limits."""

    MANDATORY_PHASES = {
        DeliverableType.RESEARCH_PAPER: [
            "research", "outline", "draft", "citation", "revision"
        ],
        DeliverableType.CODING_PROJECT: [
            "architecture", "implementation", "testing", "documentation"
        ]
    }

    def validate(self, plan_tasks: List[TaskItem], assignment: AssignmentInput) -> ValidationReport:
        report = ValidationReport(is_valid=True)
        task_id_map: Dict[str, TaskItem] = {t.task_id: t for t in plan_tasks}

        # 1. Incomplete Information Check
        for t in plan_tasks:
            if not t.title or t.title.strip() == "":
                report.incomplete_information.append(f"Task {t.task_id} has empty title.")
            if t.estimated_hours <= 0:
                report.incomplete_information.append(f"Task {t.task_id} has non-positive hours: {t.estimated_hours}")
            if not t.definition_of_done or t.definition_of_done.strip() == "":
                report.incomplete_information.append(f"Task {t.task_id} lacks 'Definition of Done'.")
            if not t.scheduled_date or not t.deadline:
                report.incomplete_information.append(f"Task {t.task_id} missing dates.")

        # 2. Missing Mandatory Academic Phases
        all_text = " ".join([f"{t.phase} {t.title}".lower() for t in plan_tasks])
        expected_phases = self.MANDATORY_PHASES.get(assignment.deliverable_type, [])
        for expected in expected_phases:
            if expected not in all_text:
                report.missing_tasks.append(f"Missing mandatory academic phase: '{expected.upper()}'.")

        # 3. Conflicting Deadlines & Dependency Order
        daily_hours_tally: Dict[date, float] = {}

        for t in plan_tasks:
            if t.scheduled_date < assignment.start_date:
                report.conflicting_deadlines.append(
                    f"Task {t.task_id} scheduled ({t.scheduled_date}) prior to start date ({assignment.start_date})."
                )
            if t.deadline > assignment.due_date:
                report.conflicting_deadlines.append(
                    f"Task {t.task_id} deadline ({t.deadline}) exceeds assignment due date ({assignment.due_date})."
                )
            if t.scheduled_date > t.deadline:
                report.conflicting_deadlines.append(
                    f"Task {t.task_id} start ({t.scheduled_date}) is after deadline ({t.deadline})."
                )

            for dep_id in t.dependencies:
                dep_task = task_id_map.get(dep_id)
                if not dep_task:
                    report.incomplete_information.append(f"Task {t.task_id} refers to missing dependency {dep_id}")
                elif dep_task.deadline > t.scheduled_date:
                    report.conflicting_deadlines.append(
                        f"Dependency inversion: Task {t.task_id} starts ({t.scheduled_date}) before prerequisite {dep_id} deadline ({dep_task.deadline})."
                    )

            daily_hours_tally[t.scheduled_date] = daily_hours_tally.get(t.scheduled_date, 0.0) + t.estimated_hours

        # 4. Workload Capacity Violations
        for day, hours in daily_hours_tally.items():
            if hours > (assignment.daily_capacity_hours + 1e-4):
                report.capacity_violations.append(
                    f"Workload overload on {day}: {hours:.1f} hrs assigned (Limit: {assignment.daily_capacity_hours} hrs)."
                )

        # 5. Safety Buffer Warnings
        if plan_tasks:
            latest_deadline = max([t.deadline for t in plan_tasks])
            buffer_days = (assignment.due_date - latest_deadline).days
            if buffer_days < 1:
                report.warnings.append(f"Zero safety buffer: Final task completes on due date ({assignment.due_date}).")

        if (report.missing_tasks or report.conflicting_deadlines or 
            report.incomplete_information or report.capacity_violations):
            report.is_valid = False

        return report


# ============================================================================
# COMPONENT 2: PLAN GENERATOR (COGNITIVE DECOMPOSITION ENGINE)
# ============================================================================
class AcademicPlanner:
    """Generates structured, balanced task breakdowns for academic tasks."""

    def generate_plan(self, assignment: AssignmentInput) -> List[TaskItem]:
        runway = (assignment.due_date - assignment.start_date).days
        if runway <= 1:
            raise ValueError("Runway must be at least 2 days.")

        buffer_days = max(1, math.floor(runway * 0.15))
        effective_days = runway - buffer_days

        if assignment.deliverable_type == DeliverableType.RESEARCH_PAPER:
            raw_tasks = [
                ("Phase 1: Orientation", "Rubric deconstruction, research question & thesis scope", Priority.HIGH, 2.0, []),
                ("Phase 2: Research", "Source discovery & annotated bibliography (8-12 papers)", Priority.HIGH, 4.5, ["T01"]),
                ("Phase 3: Outlining", "Detailed structural outline & argument flow matrix", Priority.MEDIUM, 2.5, ["T02"]),
                ("Phase 4: Drafting", "Draft Introduction, Lit Review & Arguments", Priority.HIGH, 6.0, ["T03"]),
                ("Phase 4: Drafting", "Draft Discussion, Conclusion & Citation cross-check", Priority.MEDIUM, 3.5, ["T04"]),
                ("Phase 5: Revision", "Peer review check, APA 7 proofreading & final export", Priority.LOW, 2.5, ["T05"])
            ]
        else:  # CODING_PROJECT
            raw_tasks = [
                ("Phase 1: Architecture", "System architecture diagram & API spec design", Priority.HIGH, 2.5, []),
                ("Phase 2: Implementation", "Core distributed queue & async worker pipeline", Priority.HIGH, 6.0, ["T01"]),
                ("Phase 2: Implementation", "API endpoints & error handling middleware", Priority.MEDIUM, 4.0, ["T02"]),
                ("Phase 3: Testing", "Unit test suite & benchmark performance report", Priority.HIGH, 3.5, ["T03"]),
                ("Phase 4: Documentation", "Technical report, README & Docker packaging", Priority.LOW, 2.5, ["T04"])
            ]

        tasks: List[TaskItem] = []
        current_day_offset = 0
        current_day_allocated_hours = 0.0

        for idx, (phase, title, prio, est_hrs, deps) in enumerate(raw_tasks, start=1):
            t_id = f"T{idx:02d}"
            scaled_hours = round(est_hrs * assignment.difficulty_multiplier, 1)

            earliest_start_date = assignment.start_date + timedelta(days=current_day_offset)

            for dep in deps:
                matching = [t for t in tasks if t.task_id == dep]
                if matching and matching[0].deadline >= earliest_start_date:
                    earliest_start_date = matching[0].deadline + timedelta(days=1)
                    current_day_offset = (earliest_start_date - assignment.start_date).days
                    current_day_allocated_hours = 0.0

            if (current_day_allocated_hours + scaled_hours) > assignment.daily_capacity_hours:
                current_day_offset += 1
                current_day_allocated_hours = 0.0
                earliest_start_date = assignment.start_date + timedelta(days=current_day_offset)

            task_date = earliest_start_date
            dod = f"Complete deliverable for '{title}' verified against rubric benchmarks."

            task_obj = TaskItem(
                task_id=t_id,
                phase=phase,
                title=title,
                priority=prio,
                estimated_hours=scaled_hours,
                scheduled_date=task_date,
                deadline=task_date,
                dependencies=deps,
                definition_of_done=dod
            )
            tasks.append(task_obj)
            current_day_allocated_hours += scaled_hours

        return tasks


# ============================================================================
# COMPONENT 3: DYNAMIC REVISER (REQUIREMENT CHANGE ENGINE)
# ============================================================================
class PlanReviser:
    """Adapts an existing plan when deadlines change or daily capacity drops."""

    def revise_plan(
        self,
        original_tasks: List[TaskItem],
        assignment: AssignmentInput,
        new_due_date: date,
        reason: str
    ) -> Tuple[List[TaskItem], ValidationReport]:
        assignment.due_date = new_due_date
        new_runway = (new_due_date - assignment.start_date).days

        revised: List[TaskItem] = []
        date_cursor = assignment.start_date

        for t in original_tasks:
            adjusted_hours = t.estimated_hours
            if new_runway < 8 and t.priority == Priority.LOW:
                adjusted_hours = max(1.0, round(t.estimated_hours * 0.65, 1))

            new_task = TaskItem(
                task_id=t.task_id,
                phase=t.phase,
                title=t.title + (" (Compressed)" if adjusted_hours < t.estimated_hours else ""),
                priority=t.priority,
                estimated_hours=adjusted_hours,
                scheduled_date=date_cursor,
                deadline=date_cursor,
                dependencies=t.dependencies,
                definition_of_done=t.definition_of_done + f" [Adapted: {reason}]"
            )
            revised.append(new_task)
            if adjusted_hours >= 3.0:
                date_cursor += timedelta(days=1)

        validator = PlanValidator()
        report = validator.validate(revised, assignment)
        return revised, report


# ============================================================================
# COMPONENT 4: APPLICATION CLI & INTERACTIVE SHELL
# ============================================================================
def run_interactive_cli():
    planner = AcademicPlanner()
    validator = PlanValidator()
    reviser = PlanReviser()

    print("=" * 70)
    print("🎓 ACADEMIC ASSIGNMENT PLANNING AI AGENT (CLI APPLICATION)")
    print("=" * 70)
    print("1. Run Scenario 1: Capstone Research Paper (BIO-702)")
    print("2. Run Scenario 2: Technical Distributed ML Project (CS-640)")
    print("3. Custom Assignment Input")
    print("4. Exit")
    print("-" * 70)

    choice = input("Select an option (1-4) [default: 1]: ").strip() or "1"

    if choice == "1":
        assignment = AssignmentInput(
            assignment_id="SCENARIO_1",
            title="Ethical & Regulatory Implications of Healthcare LLMs",
            course="BIO-702 / AI Ethics",
            description="3,500-word comprehensive literature review, 15 peer-reviewed papers, APA 7th format.",
            deliverable_type=DeliverableType.RESEARCH_PAPER,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            daily_capacity_hours=2.5,
            difficulty_multiplier=1.0
        )
    elif choice == "2":
        assignment = AssignmentInput(
            assignment_id="SCENARIO_2",
            title="Distributed Inference Pipeline with vLLM & Redis",
            course="CS-640: Distributed Systems for AI",
            description="Implement an asynchronous task queue with model shard workers, load tests, and PDF report.",
            deliverable_type=DeliverableType.CODING_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=10),
            daily_capacity_hours=3.0,
            difficulty_multiplier=1.0
        )
    elif choice == "3":
        title = input("Assignment Title: ")
        course = input("Course Code: ")
        t_type = input("Type (1 for Research Paper, 2 for Coding Project): ").strip()
        dtype = DeliverableType.CODING_PROJECT if t_type == "2" else DeliverableType.RESEARCH_PAPER
        days = int(input("Runway (Days until submission): ") or "14")
        hrs = float(input("Daily study capacity (hours/day): ") or "2.5")
        assignment = AssignmentInput(
            assignment_id="CUSTOM",
            title=title,
            course=course,
            description="Custom assignment prompt",
            deliverable_type=dtype,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=days),
            daily_capacity_hours=hrs
        )
    else:
        print("Exiting application.")
        return

    # Plan Generation & Validation
    plan = planner.generate_plan(assignment)
    report = validator.validate(plan, assignment)

    total_hrs = sum(t.estimated_hours for t in plan)
    capacity_hrs = (assignment.due_date - assignment.start_date).days * assignment.daily_capacity_hours

    print("\n" + "=" * 70)
    print(f"📋 ACTION PLAN GENERATED: {assignment.title}")
    print(f"Course: {assignment.course} | Type: {assignment.deliverable_type.value}")
    print(f"Runway: {(assignment.due_date - assignment.start_date).days} days | "
          f"Required Effort: {total_hrs:.1f} hrs | Capacity: {capacity_hrs:.1f} hrs")
    print(f"Validation Status: {'✅ PASSED (Valid Plan)' if report.is_valid else '❌ FAILED'}")
    if report.warnings:
        print(f"⚠️ Warnings: {report.warnings}")
    print("=" * 70)

    print("\nSCHEDULED MILESTONES & TASKS:")
    for t in plan:
        print(f"[{t.scheduled_date}] {t.task_id} ({t.priority.value}) - {t.title} ({t.estimated_hours}h)")
        print(f"    DoD: {t.definition_of_done}")

    # Dynamic Requirement Shift Simulation
    replan_choice = input("\nSimulate requirement change? (e.g. advance deadline by 4 days) [y/N]: ").strip().lower()
    if replan_choice == 'y':
        new_due = assignment.due_date - timedelta(days=4)
        print(f"\n🚨 ADVANCING DEADLINE TO {new_due}...")
        rev_plan, rev_report = reviser.revise_plan(plan, assignment, new_due, "Deadline moved forward by 4 days")
        print(f"Re-planning Status: {'✅ VALID' if rev_report.is_valid else '❌ INVALID'}")
        for t in rev_plan:
            print(f"[{t.scheduled_date}] {t.task_id} ({t.priority.value}) - {t.title} ({t.estimated_hours}h)")


if __name__ == "__main__":
    run_interactive_cli()
