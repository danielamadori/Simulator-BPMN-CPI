import argparse
import copy
import logging
import os
import sys
from pathlib import Path
import shutil

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parents[1] / "src"
if not SRC_DIR.exists():
    ROOT_DIR = SCRIPT_DIR.parents[2]
    SRC_DIR = ROOT_DIR / "simulator" / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from patterns import get_patterns
from model.context import NetContext
from model.endpoints.execute.response import petri_net_to_dot
from model.region import RegionModel, RegionType
from model.status import ActivityState
from strategy.execution import get_choices
from strategy.time import TimeStrategy
from spin_visualizzation import spin_to_svg
from dot import wrap_to_dot, STATUS_PATH

_DOT_AVAILABLE = None
_DOT_WARNED = False


def _safe_name(name: str) -> str:
    safe = name.lower()
    safe = safe.replace(" ", "_")
    safe = safe.replace("+", "plus")
    safe = safe.replace("/", "_")
    safe = safe.replace("(", "")
    safe = safe.replace(")", "")
    safe = safe.replace(",", "")
    return safe


def _format_time(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _build_region_index(region_model: RegionModel) -> dict[int, RegionModel]:
    regions = {}

    def walk(node: RegionModel) -> None:
        try:
            node_id = int(node.id)
        except (TypeError, ValueError):
            node_id = node.id
        regions[node_id] = node
        if node.children:
            for child in node.children:
                walk(child)

    walk(region_model)
    # TimeStrategy expects regions[0] to be the root region.
    regions[0] = region_model
    return regions


def _init_status(region_model: RegionModel) -> dict[RegionModel, ActivityState]:
    status = {}

    def walk(node: RegionModel) -> None:
        status[node] = ActivityState.WAITING
        if node.children:
            for child in node.children:
                walk(child)

    walk(region_model)
    return status


def _active_regions_from_marking(net, marking) -> set[str]:
    active = set()
    for place in net.places:
        entry_id = getattr(place, "entry_id", None)
        if entry_id is None:
            continue
        if marking[place].token > 0:
            active.add(str(entry_id))
    return active


def _build_visual_status_by_id(status: dict[RegionModel, ActivityState]) -> dict[str, int]:
    visual = {}
    for region, state in status.items():
        if region.is_task() and state in (
            ActivityState.ACTIVE,
            ActivityState.COMPLETED,
            ActivityState.COMPLETED_WITHOUT_PASSING_OVER,
        ):
            visual[str(region.id)] = STATUS_PATH
        else:
            visual[str(region.id)] = int(state)
    return visual


def _select_loop_transition(place, transitions, marking):
    exit_transition = None
    loop_transition = None
    for transition in transitions:
        label = str(getattr(transition, "label", ""))
        if label.startswith("Exit"):
            exit_transition = transition
        elif label.startswith("Loop"):
            loop_transition = transition

    visit_limit = getattr(place, "visit_limit", None)
    if visit_limit is not None and marking[place].visit_count >= visit_limit:
        return exit_transition or transitions[0]

    return loop_transition or transitions[0]


def _choice_combinations(ctx, marking, branch_loops: bool) -> list[list]:
    choices_by_place = get_choices(ctx, marking)
    if not choices_by_place:
        return [[]]

    combos: list[list] = [[]]
    places = sorted(choices_by_place.keys(), key=lambda p: str(p.name))
    for place in places:
        transitions = sorted(choices_by_place[place], key=lambda t: str(t.name))
        region_type = transitions[0].region_type
        if region_type == RegionType.LOOP and not branch_loops:
            transitions = [_select_loop_transition(place, transitions, marking)]
        next_combos = []
        for combo in combos:
            for transition in transitions:
                next_combos.append(combo + [transition])
        combos = next_combos
    return combos


def _render_dot(dot_source: str, base_path: Path) -> None:
    import graphviz

    global _DOT_AVAILABLE, _DOT_WARNED

    if _DOT_AVAILABLE is None:
        if shutil.which("dot") is None:
            candidates = [
                Path(os.environ.get("GRAPHVIZ_DOT", "")),
                Path(r"C:\Program Files\Graphviz\bin\dot.exe"),
                Path(r"C:\Program Files (x86)\Graphviz\bin\dot.exe"),
            ]
            for candidate in candidates:
                if candidate and candidate.exists():
                    os.environ["PATH"] = f"{candidate.parent}{os.pathsep}{os.environ.get('PATH', '')}"
                    break
        _DOT_AVAILABLE = shutil.which("dot") is not None

    if not _DOT_AVAILABLE:
        dot_path = base_path.with_suffix(".dot")
        dot_path.write_text(dot_source, encoding="utf-8")
        svg_path = base_path.with_suffix(".svg")
        if not _DOT_WARNED:
            _DOT_WARNED = True
            print("[WARN] Graphviz not found. Writing DOT files and placeholder SVGs.")
        svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="120">'
            '<rect width="100%" height="100%" fill="#ffffff"/>'
            '<text x="20" y="40" font-family="Arial" font-size="14">'
            'Graphviz not found. Install it to render this diagram.'
            '</text></svg>',
            encoding="utf-8",
        )
        return

    graph = graphviz.Source(dot_source)
    graph.render(filename=str(base_path), format="svg", cleanup=True)
    # PNG output disabled for now.


def _suppress_graphviz_warnings() -> None:
    if shutil.which("dot") is None:
        logging.getLogger("model.endpoints.execute.response").setLevel(logging.ERROR)


def _create_scenario_dirs(pattern_dir: Path, scenario_id: int) -> tuple[Path, Path, Path, Path]:
    scenario_label = f"scenario_{scenario_id:03d}"
    scenario_dir = pattern_dir / scenario_label
    spin_dir = scenario_dir / "spin"
    bpmn_dir = scenario_dir / "bpmn"
    petri_dir = scenario_dir / "petri_net"
    spin_dir.mkdir(parents=True, exist_ok=True)
    bpmn_dir.mkdir(parents=True, exist_ok=True)
    petri_dir.mkdir(parents=True, exist_ok=True)
    return scenario_dir, spin_dir, bpmn_dir, petri_dir


def _clone_scenario_dir(src_dir: Path, dst_dir: Path) -> None:
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def _save_spin(net, region_model, marking, base_path: Path, width: int, height: int) -> None:
    svg_content = spin_to_svg(net, width=width, height=height, region=region_model, marking=marking)
    svg_path = base_path.with_suffix(".svg")
    svg_path.write_text(svg_content, encoding="utf-8")
    # PNG output disabled for now.


def _save_bpmn(region_json, impacts_names, active_regions, status_by_id, base_path: Path) -> None:
    bpmn_dot = wrap_to_dot(
        region_json,
        impacts_names=impacts_names,
        active_regions=active_regions,
        status_by_id=status_by_id,
    )
    _render_dot(bpmn_dot, base_path)


def _save_petri_net(net, marking, final_marking, base_path: Path) -> None:
    dot_source = petri_net_to_dot(net, marking, final_marking)
    _render_dot(dot_source, base_path)


def _is_final(ctx, marking, final_marking) -> bool:
    if marking.tokens != final_marking.tokens:
        return False
    return len(ctx.semantic.enabled_transitions(ctx.net, marking)) == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulate each pattern step-by-step and export BPMN/SPIN/Petri net SVG snapshots."
    )
    parser.add_argument("--time-step", type=float, default=1.0, help="Time step for each simulation tick.")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum number of steps per pattern.")
    parser.add_argument("--output-dir", type=str, default=None, help="Root output directory.")
    parser.add_argument("--width", type=int, default=1000, help="SPIN SVG width.")
    parser.add_argument("--height", type=int, default=500, help="SPIN SVG height.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for nature/loop choices.")
    parser.add_argument("--patterns", nargs="*", default=None, help="Optional pattern names to include.")
    parser.add_argument("--branch-loops", action="store_true", help="Branch loop decisions (may explode scenarios).")
    args = parser.parse_args()

    if args.time_step <= 0:
        raise ValueError("--time-step must be > 0.")
    if args.max_steps <= 0:
        raise ValueError("--max-steps must be > 0.")

    if args.seed is not None:
        import numpy as np
        np.random.seed(args.seed)

    _suppress_graphviz_warnings()

    output_root = Path(args.output_dir) if args.output_dir else (SCRIPT_DIR / "output" / "time_steps")
    output_root.mkdir(parents=True, exist_ok=True)

    patterns = get_patterns()
    if args.patterns:
        wanted = {name.lower() for name in args.patterns}
        patterns = [p for p in patterns if p["name"].lower() in wanted]
        if not patterns:
            raise ValueError("No patterns matched --patterns input.")

    impacts_names = ["I1"]

    for pattern in patterns:
        name = pattern["name"]
        safe_name = _safe_name(name)
        pattern_dir = output_root / safe_name
        pattern_dir.mkdir(parents=True, exist_ok=True)

        region_json = pattern["json"]
        region_model = RegionModel.model_validate(region_json)
        ctx = NetContext.from_region(region_model)
        regions = _build_region_index(region_model)
        time_strategy = TimeStrategy()

        scenario_counter = 1
        queue = [{
            "id": scenario_counter,
            "marking": ctx.initial_marking,
            "status": _init_status(region_model),
            "cumulative_time": 0.0,
            "steps": 0,
            "frame_index": 0,
        }]

        while queue:
            scenario = queue.pop(0)
            scenario_id = scenario["id"]
            marking = scenario["marking"]
            status = scenario["status"]
            cumulative_time = scenario["cumulative_time"]
            steps = scenario["steps"]
            frame_index = scenario["frame_index"]

            scenario_dir, spin_dir, bpmn_dir, petri_dir = _create_scenario_dirs(
                pattern_dir, scenario_id
            )

            time_label = _format_time(cumulative_time)
            base_name = f"{safe_name}_{time_label}_f{frame_index:03d}"
            active_regions = _active_regions_from_marking(ctx.net, marking)
            status_by_id = _build_visual_status_by_id(status)
            _save_spin(ctx.net, region_model, marking, spin_dir / base_name, args.width, args.height)
            _save_bpmn(region_json, impacts_names, active_regions, status_by_id, bpmn_dir / base_name)
            _save_petri_net(ctx.net, marking, ctx.final_marking, petri_dir / base_name)

            if steps >= args.max_steps or _is_final(ctx, marking, ctx.final_marking):
                continue

            combinations = _choice_combinations(ctx, marking, args.branch_loops)

            if len(combinations) == 1:
                decisions = combinations[0]
                next_status = copy.deepcopy(status)
                new_marking, probability, impacts, step_time, applied_decisions = time_strategy.consume(
                    ctx, marking, regions, next_status, args.time_step, decisions
                )
                if step_time == 0 and new_marking == marking:
                    continue

                queue.append({
                    "id": scenario_id,
                    "marking": new_marking,
                    "status": next_status,
                    "cumulative_time": cumulative_time + step_time,
                    "steps": steps + 1,
                    "frame_index": frame_index + 1,
                })
                continue

            for decisions in combinations:
                next_status = copy.deepcopy(status)
                new_marking, probability, impacts, step_time, applied_decisions = time_strategy.consume(
                    ctx, marking, regions, next_status, args.time_step, decisions
                )
                if step_time == 0 and new_marking == marking:
                    continue

                scenario_counter += 1
                new_scenario_dir = pattern_dir / f"scenario_{scenario_counter:03d}"
                _clone_scenario_dir(scenario_dir, new_scenario_dir)
                queue.append({
                    "id": scenario_counter,
                    "marking": new_marking,
                    "status": next_status,
                    "cumulative_time": cumulative_time + step_time,
                    "steps": steps + 1,
                    "frame_index": frame_index + 1,
                })

        print(f"{name}: saved {scenario_counter} scenarios to {pattern_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
