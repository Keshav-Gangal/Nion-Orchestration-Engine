"""
Module 5: OutputFormatter
Renders the NION ORCHESTRATION MAP with high visual fidelity.
Standardizes headers, L1 strategic planning, and L2/L3 execution traces.
"""

from agent_registery import AgentRegistry
from l1_planner import Task, L1Plan
from l2_router import RoutedTask

# ─────────────────────────────────────────────
# VISUAL CONSTANTS
# ─────────────────────────────────────────────

SEP_FULL   = "=" * 70  # Long separator for major headers
SEP_HEADER = "=" * 12  # Section-specific separator


class OutputFormatter:

    @classmethod
    def render(
        cls,
        message: dict,
        plan: L1Plan,
        routed_tasks: list[RoutedTask],
    ) -> str:
        """Main rendering pipeline for the orchestration map."""
        lines: list[str] = []

        # 1. Header Information
        lines += cls._header(message, plan)
        
        # 2. Strategic L1 Plan
        lines += cls._l1_plan(plan)
        
        # 3. Detailed L2/L3 Execution Trace
        lines += cls._l2l3_execution(routed_tasks, message)

        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # HEADER RENDERING
    # ─────────────────────────────────────────────

    @classmethod
    def _header(cls, message: dict, plan: L1Plan) -> list[str]:
        msg_id  = message.get("message_id", "UNKNOWN")
        sender  = message.get("sender", {})
        name    = sender.get("name", "Unknown")
        role    = sender.get("role", "Unknown")
        
        project = message.get("project")
        if not project or "MISSING_PROJECT" in plan.gaps:
            project_display = "[!] MISSING - CLARIFICATION REQUIRED"
        else:
            project_display = project

        return [
            SEP_FULL,
            SEP_HEADER,
            "NION ORCHESTRATION MAP",
            SEP_FULL,
            SEP_HEADER,
            "",
            f"Message: {msg_id}",
            f"From: {name} ({role})",
            f"Project: {project_display}",
            "",
        ]

    # ─────────────────────────────────────────────
    # L1 STRATEGIC PLAN RENDERING
    # ─────────────────────────────────────────────

    @classmethod
    def _l1_plan(cls, plan: L1Plan) -> list[str]:
        """Renders the high-level orchestration strategy."""
        lines = [
            SEP_FULL,
            SEP_HEADER,
            "L1 PLAN",
            SEP_FULL,
            SEP_HEADER,
            "",
        ]

        for task in plan.tasks:
            target_label = task.display_target
            
            lines.append(f"[{task.task_id}] → {target_label}")
            lines.append(f"  Purpose: {task.purpose}")
            
            if task.depends_on:
                # Ensure numerical sorting for dependencies (e.g., 001, 002)
                sorted_deps = sorted(task.depends_on)
                deps = ", ".join(sorted_deps)
                lines.append(f"  Depends On: {deps}")
            
            lines.append("") # Spacing between tasks

        return lines

    # ─────────────────────────────────────────────
    # L2/L3 EXECUTION TRACE RENDERING
    # ─────────────────────────────────────────────

    @classmethod
    def _l2l3_execution(
        cls,
        routed_tasks: list[RoutedTask],
        message: dict,
    ) -> list[str]:
        """Renders the staircase execution trace with simulated outputs."""
        lines = [
            SEP_FULL,
            SEP_HEADER,
            "L2/L3 EXECUTION",
            SEP_FULL,
            SEP_HEADER,
            "",
        ]

        for rt in routed_tasks:
            task   = rt.parent_task
            agents = rt.l3_agents

            if task.is_cross_cutting:
                agent_name = agents[0] if agents else task.target
                lines += cls._cross_cutting_block(task, agent_name, message)
            else:
                lines += cls._l2_block(task, agents, message)

            lines.append("")

        return lines

    @classmethod
    def _cross_cutting_block(cls, task: Task, agent_name: str, message: dict) -> list[str]:
        """Renders execution for global/cross-cutting agents."""
        output = AgentRegistry.simulate_l3_output(agent_name, message)
        lines = [f"[{task.task_id}] L3:{agent_name} (Cross-Cutting)"]
        lines.append("  Status: COMPLETED")
        lines.append("  Output:")
        for line in output:
            lines.append(f"    {line}")
        return lines

    @classmethod
    def _l2_block(cls, task: Task, agents: list[str], message: dict) -> list[str]:
        """Renders domain coordination and sub-agent execution staircase."""
        lines = [f"[{task.task_id}] L2:{task.target}"]
        
        for idx, agent_name in enumerate(agents):
            sub_id = f"{task.task_id}-{chr(65 + idx)}"
            output = AgentRegistry.simulate_l3_output(agent_name, message)

            lines.append(f"  └─▶ [{sub_id}] L3:{agent_name}")
            lines.append("    Status: COMPLETED")
            lines.append("    Output:")
            for line in output:
                lines.append(f"      {line}")

        return lines