"""Step Browser screen — tree navigation of steps, turns, and template selection."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Tree, Button, Label

from template_filler_tui.models.methodology import Step, Turn, Template


class StepBrowserScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back to session"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="step-browser"):
            with Vertical(id="step-tree-panel"):
                yield Static(" Steps", markup=False)
                tree: Tree[Step | Turn | Template] = Tree("Methodology", id="step-tree")
                tree.show_root = False
                self._build_tree(tree)
                yield tree
            with Vertical(id="step-detail-panel"):
                yield Static("Select a step from the tree.", id="detail-text")

    def _build_tree(self, tree: Tree) -> None:
        steps = self.app.steps
        # Group steps by top-level parent
        current_parent_node = None
        current_parent_id = None

        for step in steps:
            if not step.has_templates:
                # Non-template steps may serve as parent headers
                if step.id == step.parent_id or not step.parent_id:
                    current_parent_node = tree.root.add(
                        f"Step {step.id}: {step.title}",
                        data=step,
                    )
                    current_parent_id = step.id
                continue

            # Determine where to add this step
            if step.parent_id and step.parent_id == current_parent_id and current_parent_node:
                step_node = current_parent_node.add(
                    f"Step {step.id}: {step.title}",
                    data=step,
                )
            else:
                step_node = tree.root.add(
                    f"Step {step.id}: {step.title}",
                    data=step,
                )
                if not step.parent_id or step.parent_id == step.id:
                    current_parent_node = step_node
                    current_parent_id = step.id

            # Add turns
            for turn in step.turns:
                if len(turn.templates) == 1:
                    step_node.add_leaf(
                        f"Turn {turn.number}: {turn.title}",
                        data=turn.templates[0],
                    )
                else:
                    turn_node = step_node.add(
                        f"Turn {turn.number}: {turn.title}",
                        data=turn,
                    )
                    for tmpl in turn.templates:
                        turn_node.add_leaf(
                            f"[{tmpl.label}]",
                            data=tmpl,
                        )

            # Add standalone templates
            for tmpl in step.standalone_templates:
                label = tmpl.label if tmpl.label != "default" else "Template"
                step_node.add_leaf(label, data=tmpl)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data

        if isinstance(node_data, Template):
            from template_filler_tui.screens.template_fill import TemplateFillScreen
            # Find step context for header
            parent = event.node.parent
            step_label = ""
            while parent:
                if isinstance(parent.data, Step):
                    step_label = f"Step {parent.data.id}: {parent.data.title}"
                    break
                parent = parent.parent
            self.app.push_screen(
                TemplateFillScreen(node_data, step_label=step_label)
            )
        elif isinstance(node_data, Step):
            detail = self.query_one("#detail-text", Static)
            info = f"Step {node_data.id}: {node_data.title}\n\n"
            n_turns = len(node_data.turns)
            n_standalone = len(node_data.standalone_templates)
            if n_turns:
                info += f"{n_turns} turn(s)\n"
            if n_standalone:
                info += f"{n_standalone} standalone template(s)\n"
            info += "\nExpand the tree to select a template."
            detail.update(info)
        elif isinstance(node_data, Turn):
            detail = self.query_one("#detail-text", Static)
            info = f"Turn {node_data.number}: {node_data.title}\n\n"
            info += f"{len(node_data.templates)} template variant(s)\n"
            info += "\nSelect a variant below."
            detail.update(info)

    def action_go_back(self) -> None:
        from template_filler_tui.screens.session_setup import SessionSetupScreen
        self.app.switch_screen(SessionSetupScreen())
