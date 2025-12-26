"""
SVG Test: Generate SVG for different Petri net patterns
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from svg_viz import petri_net_to_svg, save_svg, RegionNode
from model.petri_net.wrapper import WrapperPetriNet

def create_single_task():
    """Single task: Start -> R1 -> End"""
    net = WrapperPetriNet(name="single_task")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"  # Same as other patterns
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 5.0
    t1.impacts = [1.0, -0.5, 0.3]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"  # Same as other patterns
    
    net.places.add(p_start)
    net.places.add(p_end)
    net.transitions.add(t1)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p_end))
    
    return net

def create_sequence_two_tasks():
    """Two tasks in sequence: Start -> R1 -> p_middle -> R2 -> End"""
    net = WrapperPetriNet(name="sequence_two")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="Task A")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 5.0
    t1.impacts = [1.0, -0.5]
    
    p_middle = WrapperPetriNet.Place("p_middle")
    p_middle.entry_id = "middle_id"  # Input to Task B
    
    t2 = WrapperPetriNet.Transition("t2", label="Task B")
    t2.set_region_type("task")
    t2.set_region_label("R2")
    t2.duration = 3.0
    t2.impacts = [0.2, 0.8]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    net.places.add(p_start)
    net.places.add(p_middle)
    net.places.add(p_end)
    net.transitions.add(t1)
    net.transitions.add(t2)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p_middle))
    net.arcs.add(WrapperPetriNet.Arc(p_middle, t2))
    net.arcs.add(WrapperPetriNet.Arc(t2, p_end))
    
    return net


def create_choice():
    """Choice: Start -> (branch A -> R1 -> Exit | branch B -> R2 -> Exit) -> End"""
    net = WrapperPetriNet(name="choice")
    
    # Start place (R) - branches split from here
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Branch A: split (orange, no label)
    t_split_a = WrapperPetriNet.Transition("split_a", label="")
    t_split_a.set_region_type("choice")
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"  # Entry to task R1
    t_task_a = WrapperPetriNet.Transition("task_a", label="R1")
    t_task_a.set_region_type("task")
    t_task_a.set_region_label("R1")
    t_task_a.duration = 5.0
    t_task_a.impacts = [1.0, -0.5]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"  # Exit from task R1
    t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
    t_exit_a.set_region_type("choice_exit")  # Orange filled
    
    # Branch B: split (orange, no label)
    t_split_b = WrapperPetriNet.Transition("split_b", label="")
    t_split_b.set_region_type("choice")
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"  # Entry to task R2
    t_task_b = WrapperPetriNet.Transition("task_b", label="R2")
    t_task_b.set_region_type("task")
    t_task_b.set_region_label("R2")
    t_task_b.duration = 3.0
    t_task_b.impacts = [0.2, 0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"  # Exit from task R2
    t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
    t_exit_b.set_region_type("choice_exit")  # Orange filled
    
    # End place (R)
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add to net
    net.places.add(p_start)
    net.places.add(p_a)
    net.places.add(p_a_end)
    net.places.add(p_b)
    net.places.add(p_b_end)
    net.places.add(p_end)
    net.transitions.add(t_split_a)
    net.transitions.add(t_task_a)
    net.transitions.add(t_exit_a)
    net.transitions.add(t_split_b)
    net.transitions.add(t_task_b)
    net.transitions.add(t_exit_b)
    
    # Arcs - branch directly from start
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_split_a))
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_split_b))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(t_split_a, p_a))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_task_a))
    net.arcs.add(WrapperPetriNet.Arc(t_task_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_exit_a))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p_end))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(t_split_b, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_task_b))
    net.arcs.add(WrapperPetriNet.Arc(t_task_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_exit_b))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p_end))
    
    return net



def create_parallel():
    """Parallel: Start -> Split (+) -> (R1 AND R2) -> Join (+) -> End"""
    net = WrapperPetriNet(name="parallel")
    
    # Start place (R)
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Split transition (parallel gateway)
    t_split = WrapperPetriNet.Transition("split", label="+")
    t_split.set_region_type("parallel_split")  # Outline
    
    # Branch A: task R1
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"  # Entry to task R1
    t_task_a = WrapperPetriNet.Transition("task_a", label="R1")
    t_task_a.set_region_type("task")
    t_task_a.set_region_label("R1")
    t_task_a.duration = 5.0
    t_task_a.impacts = [1.0, -0.5]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"  # Exit from task R1
    
    # Branch B: task R2
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"  # Entry to task R2
    t_task_b = WrapperPetriNet.Transition("task_b", label="R2")
    t_task_b.set_region_type("task")
    t_task_b.set_region_label("R2")
    t_task_b.duration = 3.0
    t_task_b.impacts = [0.2, 0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"  # Exit from task R2
    
    # Join transition
    t_join = WrapperPetriNet.Transition("join", label="+")
    t_join.set_region_type("parallel_join")  # Filled black
    
    # End place (R)
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add to net
    net.places.add(p_start)
    net.places.add(p_a)
    net.places.add(p_a_end)
    net.places.add(p_b)
    net.places.add(p_b_end)
    net.places.add(p_end)
    net.transitions.add(t_split)
    net.transitions.add(t_task_a)
    net.transitions.add(t_task_b)
    net.transitions.add(t_join)
    
    # Arcs
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
    # Both branches from split
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_a))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_b))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_task_a))
    net.arcs.add(WrapperPetriNet.Arc(t_task_a, p_a_end))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_task_b))
    net.arcs.add(WrapperPetriNet.Arc(t_task_b, p_b_end))
    # Join
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))
    
    return net




def create_loop():
    """Loop matching reference: Entry -> R1 -> (π loop back | 1-π exit) -> Exit"""
    net = WrapperPetriNet(name="loop")
    
    # Start place (R label)
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Triangle 1: Entry (green filled)
    t_entry = WrapperPetriNet.Transition("entry", label="")
    t_entry.set_region_type("loop_entry")  # Green filled
    
    # Place after entry
    p_before_task = WrapperPetriNet.Place("p_before_task")
    p_before_task.entry_id = "p_before_entry"  # Entry to task R1
    
    # Task R1 (inside region)
    t_task = WrapperPetriNet.Transition("task", label="R1")
    t_task.set_region_type("task")
    t_task.set_region_label("R1")
    t_task.duration = 2.0
    t_task.impacts = [0.5]
    
    # Place after task (exit from task R1)
    p_after_task = WrapperPetriNet.Place("p_after_task")
    p_after_task.exit_id = "p_after_exit"  # Exit from task R1
    
    # Triangle 2: Loop back (π) - green outline, points UP
    t_loop = WrapperPetriNet.Transition("loop_back", label="0.7")
    t_loop.set_region_type("loop_up")  # Green outline, points up
    t_loop.set_probability(0.7)
    
    # Triangle 3: Exit (0.3) - green outline, goes to end
    t_exit_prob = WrapperPetriNet.Transition("exit_prob", label="0.3")
    t_exit_prob.set_region_type("loop")  # Green outline
    t_exit_prob.set_probability(0.3)
    
    # End place (R label)
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add to net
    net.places.add(p_start)
    net.places.add(p_before_task)
    net.places.add(p_after_task)
    net.places.add(p_end)
    net.transitions.add(t_entry)
    net.transitions.add(t_task)
    net.transitions.add(t_loop)
    net.transitions.add(t_exit_prob)
    
    # Arcs
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_entry))
    net.arcs.add(WrapperPetriNet.Arc(t_entry, p_before_task))
    net.arcs.add(WrapperPetriNet.Arc(p_before_task, t_task))
    net.arcs.add(WrapperPetriNet.Arc(t_task, p_after_task))
    net.arcs.add(WrapperPetriNet.Arc(p_after_task, t_loop))  # To loop-back
    net.arcs.add(WrapperPetriNet.Arc(t_loop, p_before_task))  # Loop back
    net.arcs.add(WrapperPetriNet.Arc(p_after_task, t_exit_prob))  # To exit
    net.arcs.add(WrapperPetriNet.Arc(t_exit_prob, p_end))  # Direct to end
    
    return net



def create_nature():
    """Nature: Start -> (π -> R1 -> Exit | 1-π -> R2 -> Exit) -> End"""
    net = WrapperPetriNet(name="nature")
    
    # Start place (R) - probabilities branch from here
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Branch A: π probability
    t_prob_a = WrapperPetriNet.Transition("prob_a", label="0.6")
    t_prob_a.set_region_type("nature")
    t_prob_a.set_probability(0.6)
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"  # Entry to task R1
    t_task_a = WrapperPetriNet.Transition("task_a", label="R1")
    t_task_a.set_region_type("task")
    t_task_a.set_region_label("R1")
    t_task_a.duration = 5.0
    t_task_a.impacts = [1.0, -0.5]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"  # Exit from task R1
    t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
    t_exit_a.set_region_type("nature_exit")  # Green filled
    
    # Branch B: 1-π probability
    t_prob_b = WrapperPetriNet.Transition("prob_b", label="0.4")
    t_prob_b.set_region_type("nature")
    t_prob_b.set_probability(0.4)
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"  # Entry to task R2
    t_task_b = WrapperPetriNet.Transition("task_b", label="R2")
    t_task_b.set_region_type("task")
    t_task_b.set_region_label("R2")
    t_task_b.duration = 3.0
    t_task_b.impacts = [0.2, 0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"  # Exit from task R2
    t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
    t_exit_b.set_region_type("nature_exit")  # Green filled
    
    # End place (R)
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add to net
    net.places.add(p_start)
    net.places.add(p_a)
    net.places.add(p_a_end)
    net.places.add(p_b)
    net.places.add(p_b_end)
    net.places.add(p_end)
    net.transitions.add(t_prob_a)
    net.transitions.add(t_task_a)
    net.transitions.add(t_exit_a)
    net.transitions.add(t_prob_b)
    net.transitions.add(t_task_b)
    net.transitions.add(t_exit_b)
    
    # Arcs - branch directly from start
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_prob_a))
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_prob_b))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(t_prob_a, p_a))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_task_a))
    net.arcs.add(WrapperPetriNet.Arc(t_task_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_exit_a))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p_end))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(t_prob_b, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_task_b))
    net.arcs.add(WrapperPetriNet.Arc(t_task_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_exit_b))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p_end))
    
    return net


# =============================================================================
# COMBINATION PATTERNS
# =============================================================================

def create_sequential_parallel():
    """R1, (R2 || R3), R4"""
    net = WrapperPetriNet(name="task_parallel_task")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p1 = WrapperPetriNet.Place("p1")
    p1.entry_id = "p1_entry"
    
    t_split = WrapperPetriNet.Transition("split", label="+")
    t_split.set_region_type("parallel_split")
    
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"
    t_a = WrapperPetriNet.Transition("t_a", label="R2")
    t_a.set_region_type("task")
    t_a.set_region_label("R2")
    t_a.duration = 3.0
    t_a.impacts = [1.0]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"
    
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"
    t_b = WrapperPetriNet.Transition("t_b", label="R3")
    t_b.set_region_type("task")
    t_b.set_region_label("R3")
    t_b.duration = 4.0
    t_b.impacts = [0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"
    
    t_join = WrapperPetriNet.Transition("join", label="+")
    t_join.set_region_type("parallel_join")
    
    p2 = WrapperPetriNet.Place("p2")
    p2.entry_id = "p2_entry"
    
    t4 = WrapperPetriNet.Transition("t4", label="R4")
    t4.set_region_type("task")
    t4.set_region_label("R4")
    t4.duration = 1.0
    t4.impacts = [0.2]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    for p in [p_start, p1, p_a, p_a_end, p_b, p_b_end, p2, p_end]:
        net.places.add(p)
    for t in [t1, t_split, t_a, t_b, t_join, t4]:
        net.transitions.add(t)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p1))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_split))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_a))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_a))
    net.arcs.add(WrapperPetriNet.Arc(t_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_b))
    net.arcs.add(WrapperPetriNet.Arc(t_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(t_join, p2))
    net.arcs.add(WrapperPetriNet.Arc(p2, t4))
    net.arcs.add(WrapperPetriNet.Arc(t4, p_end))
    
    # Build region tree: Sequential:0 > (Sequential:1 > (R1, Parallel:3 > (R2, R3)), R4)
    # Task nodes with their associated elements (transition + entry/exit places)
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start', 'p1'])
    r2_node = RegionNode('task', 4, 'R2', elements=['t_a', 'p_a', 'p_a_end'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_b', 'p_b', 'p_b_end'])
    r4_node = RegionNode('task', 6, 'R4', elements=['t4', 'p2', 'end'])
    
    # Parallel node containing R2 and R3 - includes p1 (shared entry) and p2 (shared exit)
    parallel_node = RegionNode('parallel', 3, 'R2 || R3', 
                                children=[r2_node, r3_node],
                                elements=['split', 'join', 'p1', 'p2'])
    
    # Flat Sequential containing R1, Parallel, and R4 (ensures shared borders)
    seq0_node = RegionNode('sequential', 0, 'R1, (R2 || R3), R4', 
                           children=[r1_node, parallel_node, r4_node])
    
    return net, seq0_node


def create_sequential_choice():
    """R1, (R2 /[C1] R3), R4"""
    net = WrapperPetriNet(name="task_choice_task")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p1 = WrapperPetriNet.Place("p1")
    p1.entry_id = "p1_entry"
    
    t_split_a = WrapperPetriNet.Transition("split_a", label="")
    t_split_a.set_region_type("choice")
    t_split_b = WrapperPetriNet.Transition("split_b", label="")
    t_split_b.set_region_type("choice")
    
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"
    t_a = WrapperPetriNet.Transition("t_a", label="R2")
    t_a.set_region_type("task")
    t_a.set_region_label("R2")
    t_a.duration = 3.0
    t_a.impacts = [1.0]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"
    t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
    t_exit_a.set_region_type("choice_exit")
    
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"
    t_b = WrapperPetriNet.Transition("t_b", label="R3")
    t_b.set_region_type("task")
    t_b.set_region_label("R3")
    t_b.duration = 4.0
    t_b.impacts = [0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"
    t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
    t_exit_b.set_region_type("choice_exit")
    
    p2 = WrapperPetriNet.Place("p2")
    p2.entry_id = "p2_entry"
    
    t4 = WrapperPetriNet.Transition("t4", label="R4")
    t4.set_region_type("task")
    t4.set_region_label("R4")
    t4.duration = 1.0
    t4.impacts = [0.2]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    for p in [p_start, p1, p_a, p_a_end, p_b, p_b_end, p2, p_end]:
        net.places.add(p)
    for t in [t1, t_split_a, t_split_b, t_a, t_b, t_exit_a, t_exit_b, t4]:
        net.transitions.add(t)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p1))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_split_a))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_split_b))
    net.arcs.add(WrapperPetriNet.Arc(t_split_a, p_a))
    net.arcs.add(WrapperPetriNet.Arc(t_split_b, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_a))
    net.arcs.add(WrapperPetriNet.Arc(t_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_exit_a))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_b))
    net.arcs.add(WrapperPetriNet.Arc(t_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_exit_b))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p2))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p2))
    net.arcs.add(WrapperPetriNet.Arc(p2, t4))
    net.arcs.add(WrapperPetriNet.Arc(t4, p_end))
    
    # Build region tree
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start', 'p1'])
    r2_node = RegionNode('task', 4, 'R2', elements=['t_a', 'p_a', 'p_a_end'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_b', 'p_b', 'p_b_end'])
    r4_node = RegionNode('task', 6, 'R4', elements=['t4', 'p2', 'end'])
    
    # Choice node containing R2 and R3
    choice_node = RegionNode('choice', 3, 'R2 /[C1] R3', 
                             children=[r2_node, r3_node],
                             elements=['split_a', 'split_b', 'exit_a', 'exit_b', 'p1', 'p2'])
    
    # Flat Sequential containing R1, Choice, and R4 (ensures shared borders)
    seq0_node = RegionNode('sequential', 0, 'R1, (R2 /[C1] R3), R4', 
                           children=[r1_node, choice_node, r4_node])
    
    return net, seq0_node


def create_sequential_loop():
    """R1, <R2 [L1]>"""
    net = WrapperPetriNet(name="task_loop")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p1 = WrapperPetriNet.Place("p1")
    p1.entry_id = "p1_entry"
    
    t_entry = WrapperPetriNet.Transition("entry", label="")
    t_entry.set_region_type("loop_entry")
    
    p_before = WrapperPetriNet.Place("p_before")
    p_before.entry_id = "p_before_entry"
    
    t2 = WrapperPetriNet.Transition("t2", label="R2")
    t2.set_region_type("task")
    t2.set_region_label("R2")
    t2.duration = 3.0
    t2.impacts = [1.0]
    
    p_after = WrapperPetriNet.Place("p_after")
    p_after.exit_id = "p_after_exit"
    
    t_loop = WrapperPetriNet.Transition("loop_back", label="0.7")
    t_loop.set_region_type("loop_up")
    t_loop.set_probability(0.7)
    
    t_exit = WrapperPetriNet.Transition("exit", label="0.3")
    t_exit.set_region_type("loop")
    t_exit.set_probability(0.3)
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    for p in [p_start, p1, p_before, p_after, p_end]:
        net.places.add(p)
    for t in [t1, t_entry, t2, t_loop, t_exit]:
        net.transitions.add(t)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p1))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_entry))
    net.arcs.add(WrapperPetriNet.Arc(t_entry, p_before))
    net.arcs.add(WrapperPetriNet.Arc(p_before, t2))
    net.arcs.add(WrapperPetriNet.Arc(t2, p_after))
    net.arcs.add(WrapperPetriNet.Arc(p_after, t_loop))
    net.arcs.add(WrapperPetriNet.Arc(t_loop, p_before))
    net.arcs.add(WrapperPetriNet.Arc(p_after, t_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_exit, p_end))
    
    # Build region tree
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start', 'p1'])
    r2_node = RegionNode('task', 4, 'R2', elements=['t2', 'p_before', 'p_after'])
    
    # Loop node containing R2
    loop_node = RegionNode('loop', 3, '<R2 [L1]>', 
                           children=[r2_node],
                           elements=['entry', 'loop_back', 'exit', 'p1', 'end'])
    
    # Outer Sequential
    seq0_node = RegionNode('sequential', 0, 'R1, <R2 [L1]>', 
                           children=[r1_node, loop_node])
    
    return net, seq0_node


def create_sequential_nature():
    """R1, ^[N1]"""
    net = WrapperPetriNet(name="task_nature")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p1 = WrapperPetriNet.Place("p1")
    p1.entry_id = "p1_entry"
    
    # Branch A: π probability
    t_prob_a = WrapperPetriNet.Transition("prob_a", label="0.6")
    t_prob_a.set_region_type("nature")
    t_prob_a.set_probability(0.6)
    
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"
    t_a = WrapperPetriNet.Transition("t_a", label="R2")
    t_a.set_region_type("task")
    t_a.set_region_label("R2")
    t_a.duration = 3.0
    t_a.impacts = [1.0]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"
    t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
    t_exit_a.set_region_type("nature_exit")
    
    # Branch B: 1-π probability
    t_prob_b = WrapperPetriNet.Transition("prob_b", label="0.4")
    t_prob_b.set_region_type("nature")
    t_prob_b.set_probability(0.4)
    
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"
    t_b = WrapperPetriNet.Transition("t_b", label="R3")
    t_b.set_region_type("task")
    t_b.set_region_label("R3")
    t_b.duration = 4.0
    t_b.impacts = [0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"
    t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
    t_exit_b.set_region_type("nature_exit")
    
    p2 = WrapperPetriNet.Place("p2")
    p2.entry_id = "p2_entry"
    
    t4 = WrapperPetriNet.Transition("t4", label="R4")
    t4.set_region_type("task")
    t4.set_region_label("R4")
    t4.duration = 1.0
    t4.impacts = [0.2]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    for p in [p_start, p1, p_a, p_a_end, p_b, p_b_end, p2, p_end]:
        net.places.add(p)
    for t in [t1, t_prob_a, t_prob_b, t_a, t_b, t_exit_a, t_exit_b, t4]:
        net.transitions.add(t)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p1))
    # Nature split
    net.arcs.add(WrapperPetriNet.Arc(p1, t_prob_a))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_prob_b))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(t_prob_a, p_a))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_a))
    net.arcs.add(WrapperPetriNet.Arc(t_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_exit_a))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(t_prob_b, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_b))
    net.arcs.add(WrapperPetriNet.Arc(t_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_exit_b))
    # Nature join
    net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p2))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p2))
    
    net.arcs.add(WrapperPetriNet.Arc(p2, t4))
    net.arcs.add(WrapperPetriNet.Arc(t4, p_end))
    
    # Build region tree
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start', 'p1'])
    r2_node = RegionNode('task', 4, 'R2', elements=['t_a', 'p_a', 'p_a_end'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_b', 'p_b', 'p_b_end'])
    r4_node = RegionNode('task', 6, 'R4', elements=['t4', 'p2', 'end'])
    
    # Nature node containing R2 and R3
    nature_node = RegionNode('nature', 3, '^[N1]', 
                             children=[r2_node, r3_node],
                             elements=['prob_a', 'prob_b', 'exit_a', 'exit_b', 'p1', 'p2'])
    
    # Inner Sequential containing R1 and Nature
    seq1_node = RegionNode('sequential', 1, 'R1, ^[N1]', 
                           children=[r1_node, nature_node])
    
    # Outer Sequential
    seq0_node = RegionNode('sequential', 0, 'R1, ^[N1], R4', 
                           children=[seq1_node, r4_node])
    
    return net, seq0_node


def create_sequential_nature():
    """R1, ^[N1]"""
    net = WrapperPetriNet(name="task_nature")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p1 = WrapperPetriNet.Place("p1_end")
    p1.entry_id = "p1_entry"
    
    # Branch A: π probability
    t_prob_a = WrapperPetriNet.Transition("prob_a", label="0.6")
    t_prob_a.set_region_type("nature")
    t_prob_a.set_probability(0.6)
    
    p_a = WrapperPetriNet.Place("p_a")
    p_a.entry_id = "p_a_entry"
    t_a = WrapperPetriNet.Transition("t_a", label="R2")
    t_a.set_region_type("task")
    t_a.set_region_label("R2")
    t_a.duration = 3.0
    t_a.impacts = [1.0]
    p_a_end = WrapperPetriNet.Place("p_a_end")
    p_a_end.exit_id = "p_a_exit"
    t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
    t_exit_a.set_region_type("nature_exit")
    
    # Branch B: 1-π probability
    t_prob_b = WrapperPetriNet.Transition("prob_b", label="0.4")
    t_prob_b.set_region_type("nature")
    t_prob_b.set_probability(0.4)
    
    p_b = WrapperPetriNet.Place("p_b")
    p_b.entry_id = "p_b_entry"
    t_b = WrapperPetriNet.Transition("t_b", label="R3")
    t_b.set_region_type("task")
    t_b.set_region_label("R3")
    t_b.duration = 4.0
    t_b.impacts = [0.8]
    p_b_end = WrapperPetriNet.Place("p_b_end")
    p_b_end.exit_id = "p_b_exit"
    t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
    t_exit_b.set_region_type("nature_exit")
    
    p2 = WrapperPetriNet.Place("p2")
    p2.entry_id = "p2_entry"
    
    t4 = WrapperPetriNet.Transition("t4", label="R4")
    t4.set_region_type("task")
    t4.set_region_label("R4")
    t4.duration = 1.0
    t4.impacts = [0.2]
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    for p in [p_start, p1, p_a, p_a_end, p_b, p_b_end, p2, p_end]:
        net.places.add(p)
    for t in [t1, t_prob_a, t_prob_b, t_a, t_b, t_exit_a, t_exit_b, t4]:
        net.transitions.add(t)
    
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p1))
    # Nature split
    net.arcs.add(WrapperPetriNet.Arc(p1, t_prob_a))
    net.arcs.add(WrapperPetriNet.Arc(p1, t_prob_b))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(t_prob_a, p_a))
    net.arcs.add(WrapperPetriNet.Arc(p_a, t_a))
    net.arcs.add(WrapperPetriNet.Arc(t_a, p_a_end))
    net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_exit_a))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(t_prob_b, p_b))
    net.arcs.add(WrapperPetriNet.Arc(p_b, t_b))
    net.arcs.add(WrapperPetriNet.Arc(t_b, p_b_end))
    net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_exit_b))
    # Nature join
    net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p2))
    net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p2))
    
    net.arcs.add(WrapperPetriNet.Arc(p2, t4))
    net.arcs.add(WrapperPetriNet.Arc(t4, p_end))
    
    # Build region tree
    
    # R1 leaf (excluding p1_end to avoid box stretching)
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start'])
    
    # R2 and R3 leaves (branches)
    r2_node = RegionNode('task', 4, 'R2', elements=['t_a', 'p_a', 'p_a_end'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_b', 'p_b', 'p_b_end'])
    
    # R4 leaf (excluding p2 to avoid box stretching)
    # p2 is entry to R4? No, p2 is input to t4. 
    # Wait, p2 is OUTPUT of Nature.
    # User didn't complain about p2. But if they want consistency...
    # p2 connects Nature to R4.
    # It is on Nature's right border (cut in half).
    # Is it black? It is named "p2". Not black.
    # Does user want p2 black too?
    # User said: "posto in uscita di task1". p1 explicitly.
    # p2 is output of Nature. Maybe Nature outputs are not black?
    # R1 output -> p1.
    # I'll stick to p1 for now.
    
    r4_node = RegionNode('task', 6, 'R4', elements=['t4', 'end'])
    
    # Nature Node (^[N1]) containing R2 and R3 (Split regions)
    # Nature OWNS the shared connection places p1_end and p2
    nature_node = RegionNode('nature', 3, 'R2 ^[N1] R3', 
                             children=[r2_node, r3_node],
                             elements=['prob_a', 'prob_b', 'exit_a', 'exit_b', 'p1_end', 'p2']) # p1 renamed here too

                             
    # Root Sequential: R1, Nature, R4
    seq0_node = RegionNode('sequential', 0, 'R1, (R2 ^[N1] R3), R4', 
                           children=[r1_node, nature_node, r4_node])
    
    return net, seq0_node





def create_complex_parallel():
    """R1, ((R2 /[C1] R3) || <R4 [L1]>), R5"""
    net = WrapperPetriNet(name="complex_parallel")
    
    # 1. Start R1
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t1 = WrapperPetriNet.Transition("t1", label="R1")
    t1.set_region_type("task")
    t1.set_region_label("R1")
    t1.duration = 2.0
    t1.impacts = [0.5]
    
    p_pre_split = WrapperPetriNet.Place("p_pre_split")
    p_pre_split.entry_id = "p_pre_split_entry"
    
    # 2. Parallel Split
    t_split = WrapperPetriNet.Transition("split", label="+")
    t_split.set_region_type("parallel_split")
    
    p_choice_start = WrapperPetriNet.Place("p_choice_start") # Branch 1 start
    p_loop_start = WrapperPetriNet.Place("p_loop_start")     # Branch 2 start
    
    # --- Branch 1: Choice (R2 /[C1] R3) ---
    # Detailed split/exit structure for visualization
    
    # R2 Branch
    t_c1_split = WrapperPetriNet.Transition("t_c1_split", label="")
    t_c1_split.set_region_type("choice")
    p_c1_in = WrapperPetriNet.Place("p_c1_in")
    
    t_c1 = WrapperPetriNet.Transition("t_c1", label="R2")
    t_c1.set_region_type("task")
    t_c1.set_region_label("R2")
    t_c1.duration = 3.0
    
    p_c1_out = WrapperPetriNet.Place("p_c1_out")
    t_c1_exit = WrapperPetriNet.Transition("t_c1_exit", label="")
    t_c1_exit.set_region_type("choice_exit")
    
    # R3 Branch
    t_c2_split = WrapperPetriNet.Transition("t_c2_split", label="")
    t_c2_split.set_region_type("choice")
    p_c2_in = WrapperPetriNet.Place("p_c2_in")
    
    t_c2 = WrapperPetriNet.Transition("t_c2", label="R3")
    t_c2.set_region_type("task")
    t_c2.set_region_label("R3")
    t_c2.duration = 2.5
    
    p_c2_out = WrapperPetriNet.Place("p_c2_out")
    t_c2_exit = WrapperPetriNet.Transition("t_c2_exit", label="")
    t_c2_exit.set_region_type("choice_exit")
    
    p_choice_end = WrapperPetriNet.Place("p_choice_end") # Branch 1 end
    
    # --- Branch 2: Loop <R4 [L1]> ---
    t_loop_entry = WrapperPetriNet.Transition("loop_entry", label="")
    t_loop_entry.set_region_type("loop_entry")
    
    p_loop_body_start = WrapperPetriNet.Place("p_loop_body_start")
    p_loop_body_start.entry_id = "p_loop_body_entry"
    
    t_r4 = WrapperPetriNet.Transition("t_r4", label="R4")
    t_r4.set_region_type("task")
    t_r4.set_region_label("R4")
    t_r4.duration = 1.5
    
    p_loop_body_end = WrapperPetriNet.Place("p_loop_body_end")
    p_loop_body_end.exit_id = "p_loop_body_exit"
    
    t_loop_back = WrapperPetriNet.Transition("loop_back", label="0.3")
    t_loop_back.set_region_type("loop_up")
    t_loop_back.set_probability(0.3)
    
    t_loop_exit = WrapperPetriNet.Transition("loop_exit", label="0.7")
    t_loop_exit.set_region_type("loop_exit")
    t_loop_exit.set_probability(0.7)
    
    p_loop_end = WrapperPetriNet.Place("p_loop_end") # Branch 2 end
    
    # 3. Parallel Join
    t_join = WrapperPetriNet.Transition("join", label="+")
    t_join.set_region_type("parallel_join")
    
    p_post_join = WrapperPetriNet.Place("p_post_join")
    p_post_join.entry_id = "p_post_join_entry"
    
    # 4. Final R5
    t5 = WrapperPetriNet.Transition("t5", label="R5")
    t5.set_region_type("task")
    t5.set_region_label("R5")
    t5.duration = 1.0
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add elements
    for p in [p_start, p_pre_split, p_choice_start, p_loop_start, p_choice_end, 
              p_loop_body_start, p_loop_body_end, p_loop_end, p_post_join, p_end,
              p_c1_in, p_c1_out, p_c2_in, p_c2_out]:
        net.places.add(p)
        
    for t in [t1, t_split, t_c1_split, t_c1, t_c1_exit, t_c2_split, t_c2, t_c2_exit, 
              t_loop_entry, t_r4, t_loop_back, t_loop_exit, t_join, t5]:
        net.transitions.add(t)
        
    # Connections
    # R1 -> Parallel
    net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
    net.arcs.add(WrapperPetriNet.Arc(t1, p_pre_split))
    net.arcs.add(WrapperPetriNet.Arc(p_pre_split, t_split))
    
    # Split
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_choice_start))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_loop_start))
    
    # Branch 1: Choice
    # R2 path
    net.arcs.add(WrapperPetriNet.Arc(p_choice_start, t_c1_split))
    net.arcs.add(WrapperPetriNet.Arc(t_c1_split, p_c1_in))
    net.arcs.add(WrapperPetriNet.Arc(p_c1_in, t_c1))
    net.arcs.add(WrapperPetriNet.Arc(t_c1, p_c1_out))
    net.arcs.add(WrapperPetriNet.Arc(p_c1_out, t_c1_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_c1_exit, p_choice_end))
    
    # R3 path
    net.arcs.add(WrapperPetriNet.Arc(p_choice_start, t_c2_split))
    net.arcs.add(WrapperPetriNet.Arc(t_c2_split, p_c2_in))
    net.arcs.add(WrapperPetriNet.Arc(p_c2_in, t_c2))
    net.arcs.add(WrapperPetriNet.Arc(t_c2, p_c2_out))
    net.arcs.add(WrapperPetriNet.Arc(p_c2_out, t_c2_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_c2_exit, p_choice_end))
    
    # Branch 2: Loop
    net.arcs.add(WrapperPetriNet.Arc(p_loop_start, t_loop_entry))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_entry, p_loop_body_start))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_body_start, t_r4))
    net.arcs.add(WrapperPetriNet.Arc(t_r4, p_loop_body_end))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_body_end, t_loop_back))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_back, p_loop_body_start))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_body_end, t_loop_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_exit, p_loop_end))
    
    # Join -> R5
    net.arcs.add(WrapperPetriNet.Arc(p_choice_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(t_join, p_post_join))
    net.arcs.add(WrapperPetriNet.Arc(p_post_join, t5))
    net.arcs.add(WrapperPetriNet.Arc(t5, p_end))
    
    # --- Region Tree ---
    
    # Leaves
    r1_node = RegionNode('task', 2, 'R1', elements=['t1', 'start', 'p_pre_split'])
    
    r2_node = RegionNode('task', 4, 'R2', elements=['t_c1', 'p_c1_in', 'p_c1_out'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_c2', 'p_c2_in', 'p_c2_out'])
    r4_node = RegionNode('task', 6, 'R4', elements=['t_r4', 'p_loop_body_start', 'p_loop_body_end'])
    
    r5_node = RegionNode('task', 8, 'R5', elements=['t5', 'p_post_join', 'end'])
    
    # Choice Node (in parallel branch 1)
    choice_node = RegionNode('choice', 3, 'R2 /[C1] R3', 
                             children=[r2_node, r3_node],
                             elements=['p_choice_start', 'p_choice_end',
                                       't_c1_split', 't_c1_exit', 
                                       't_c2_split', 't_c2_exit'])
    
    # Loop Node (in parallel branch 2)
    loop_node = RegionNode('loop', 3, '<R4 [L1]>',
                           children=[r4_node],
                           elements=['loop_entry', 'loop_back', 'loop_exit', 'p_loop_start', 'p_loop_end'])
    
    # Parallel Node containing Choice and Loop
    parallel_node = RegionNode('parallel', 1, '((R2 /[C1] R3) || <R4 [L1]>)',
                               children=[choice_node, loop_node],
                               elements=['split', 'join', 'p_pre_split', 'p_post_join'])
                               
    # Outer Sequential
    seq_node = RegionNode('sequential', 0, 'R1, ((R2 /[C1] R3) || <R4 [L1]>), R5',
                          children=[r1_node, parallel_node, r5_node])
                          
    return net, seq_node


def create_parallel_choice_simple():
    """((R2 /[C1] R3) || R4)"""
    net = WrapperPetriNet(name="parallel_choice_simple")
    
    # 1. Start (pre-split)
    p_parallel_entry = WrapperPetriNet.Place("p_parallel_entry")
    p_parallel_entry.entry_id = "p_parallel_entry"
    
    # 2. Parallel Split
    t_split = WrapperPetriNet.Transition("split", label="+")
    t_split.set_region_type("parallel_split")
    
    p_choice_start = WrapperPetriNet.Place("p_choice_start") # Branch 1 start
    p_task_start = WrapperPetriNet.Place("p_task_start")     # Branch 2 start
    
    # --- Branch 1: Choice (R2 /[C1] R3) ---
    # We implement explicit Split/Exit transitions to match the standard Choice pattern visuals (triangles/diamonds)
    
    # Sub-branch R2
    t_c1_split = WrapperPetriNet.Transition("t_c1_split", label="")
    t_c1_split.set_region_type("choice") # Orange Triangle
    p_c1_in = WrapperPetriNet.Place("p_c1_in")
    
    t_c1 = WrapperPetriNet.Transition("t_c1", label="R2")
    t_c1.set_region_type("task")
    t_c1.set_region_label("R2")
    t_c1.duration = 3.0
    
    p_c1_out = WrapperPetriNet.Place("p_c1_out")
    t_c1_exit = WrapperPetriNet.Transition("t_c1_exit", label="")
    t_c1_exit.set_region_type("choice_exit") # Orange Filled
    
    # Sub-branch R3
    t_c2_split = WrapperPetriNet.Transition("t_c2_split", label="")
    t_c2_split.set_region_type("choice") # Orange Triangle
    p_c2_in = WrapperPetriNet.Place("p_c2_in")
    
    t_c2 = WrapperPetriNet.Transition("t_c2", label="R3")
    t_c2.set_region_type("task")
    t_c2.set_region_label("R3")
    t_c2.duration = 2.5
    
    p_c2_out = WrapperPetriNet.Place("p_c2_out")
    t_c2_exit = WrapperPetriNet.Transition("t_c2_exit", label="")
    t_c2_exit.set_region_type("choice_exit") # Orange Filled
    
    p_choice_end = WrapperPetriNet.Place("p_choice_end") # Branch 1 end
    
    # --- Branch 2: Task R4 ---
    t_r4 = WrapperPetriNet.Transition("t_r4", label="R4")
    t_r4.set_region_type("task")
    t_r4.set_region_label("R4")
    t_r4.duration = 1.5
    
    p_task_end = WrapperPetriNet.Place("p_task_end") # Branch 2 end
    
    # 3. Parallel Join
    t_join = WrapperPetriNet.Transition("join", label="+")
    t_join.set_region_type("parallel_join")
    
    p_post_join = WrapperPetriNet.Place("p_post_join")
    p_post_join.exit_id = "p_post_join_exit"
    
    # Add elements
    for p in [p_parallel_entry, p_choice_start, p_task_start, p_choice_end, p_task_end, p_post_join,
              p_c1_in, p_c1_out, p_c2_in, p_c2_out]:
        net.places.add(p)
    for t in [t_split, t_c1_split, t_c1, t_c1_exit, t_c2_split, t_c2, t_c2_exit, t_r4, t_join]:
        net.transitions.add(t)
        
    # Connections
    # Pre -> Split
    net.arcs.add(WrapperPetriNet.Arc(p_parallel_entry, t_split))
    
    # Split -> Branches
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_choice_start))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_task_start))
    
    # Branch 1: Choice
    # Path 1 (R2)
    net.arcs.add(WrapperPetriNet.Arc(p_choice_start, t_c1_split))
    net.arcs.add(WrapperPetriNet.Arc(t_c1_split, p_c1_in))
    net.arcs.add(WrapperPetriNet.Arc(p_c1_in, t_c1))
    net.arcs.add(WrapperPetriNet.Arc(t_c1, p_c1_out))
    net.arcs.add(WrapperPetriNet.Arc(p_c1_out, t_c1_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_c1_exit, p_choice_end))
    
    # Path 2 (R3)
    net.arcs.add(WrapperPetriNet.Arc(p_choice_start, t_c2_split))
    net.arcs.add(WrapperPetriNet.Arc(t_c2_split, p_c2_in))
    net.arcs.add(WrapperPetriNet.Arc(p_c2_in, t_c2))
    net.arcs.add(WrapperPetriNet.Arc(t_c2, p_c2_out))
    net.arcs.add(WrapperPetriNet.Arc(p_c2_out, t_c2_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_c2_exit, p_choice_end))
    
    # Branch 2: Task R4
    net.arcs.add(WrapperPetriNet.Arc(p_task_start, t_r4))
    net.arcs.add(WrapperPetriNet.Arc(t_r4, p_task_end))
    
    # Branches -> Join
    net.arcs.add(WrapperPetriNet.Arc(p_choice_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_task_end, t_join))
    
    # Join -> Post
    net.arcs.add(WrapperPetriNet.Arc(t_join, p_post_join))
    
    # --- Region Tree ---
    
    # Branch 1 Leaves
    # Include internal places/transitions in the leaf task regions
    r2_node = RegionNode('task', 4, 'R2', elements=['t_c1', 'p_c1_in', 'p_c1_out'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_c2', 'p_c2_in', 'p_c2_out'])
    
    # Choice Node
    # Include split/exit transitions here so they are laid out by the parent choice logic
    choice_node = RegionNode('choice', 3, 'R2 /[C1] R3', 
                             children=[r2_node, r3_node],
                             elements=['p_choice_start', 'p_choice_end', 
                                       't_c1_split', 't_c1_exit', 
                                       't_c2_split', 't_c2_exit'])
                             
    # Branch 2 Leaf
    r4_node = RegionNode('task', 6, 'R4', elements=['t_r4', 'p_task_start', 'p_task_end'])
    
    # Parallel Node
    parallel_node = RegionNode('parallel', 1, '((R2 /[C1] R3) || R4)',
                               children=[choice_node, r4_node],
                               elements=['split', 'join', 'p_parallel_entry', 'p_post_join'])
                               
    return net, parallel_node


# =============================================================================
# NEW ADVANCED PATTERN FUNCTIONS
# =============================================================================

def create_choice_of_parallels():
    """(R1 || R2) /[C1] (R3 || R4)"""
    net = WrapperPetriNet(name="choice_of_parallels")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Choice split transitions
    t_c_split1 = WrapperPetriNet.Transition("t_c_split1", label="")
    t_c_split1.set_region_type("choice")
    t_c_split2 = WrapperPetriNet.Transition("t_c_split2", label="")
    t_c_split2.set_region_type("choice")
    
    # Branch A: Parallel (R1 || R2)
    p_par1_start = WrapperPetriNet.Place("p_par1_start")
    t_par1_split = WrapperPetriNet.Transition("t_par1_split", label="+")
    t_par1_split.set_region_type("parallel_split")
    
    p_r1 = WrapperPetriNet.Place("p_r1")
    t_r1 = WrapperPetriNet.Transition("t_r1", label="R1")
    t_r1.set_region_type("task")
    t_r1.duration = 2.0
    p_r1_end = WrapperPetriNet.Place("p_r1_end")
    
    p_r2 = WrapperPetriNet.Place("p_r2")
    t_r2 = WrapperPetriNet.Transition("t_r2", label="R2")
    t_r2.set_region_type("task")
    t_r2.duration = 3.0
    p_r2_end = WrapperPetriNet.Place("p_r2_end")
    
    t_par1_join = WrapperPetriNet.Transition("t_par1_join", label="+")
    t_par1_join.set_region_type("parallel_join")
    p_par1_end = WrapperPetriNet.Place("p_par1_end")
    
    t_c_exit1 = WrapperPetriNet.Transition("t_c_exit1", label="")
    t_c_exit1.set_region_type("choice_exit")
    
    # Branch B: Parallel (R3 || R4)
    p_par2_start = WrapperPetriNet.Place("p_par2_start")
    t_par2_split = WrapperPetriNet.Transition("t_par2_split", label="+")
    t_par2_split.set_region_type("parallel_split")
    
    p_r3 = WrapperPetriNet.Place("p_r3")
    t_r3 = WrapperPetriNet.Transition("t_r3", label="R3")
    t_r3.set_region_type("task")
    t_r3.duration = 1.5
    p_r3_end = WrapperPetriNet.Place("p_r3_end")
    
    p_r4 = WrapperPetriNet.Place("p_r4")
    t_r4 = WrapperPetriNet.Transition("t_r4", label="R4")
    t_r4.set_region_type("task")
    t_r4.duration = 2.5
    p_r4_end = WrapperPetriNet.Place("p_r4_end")
    
    t_par2_join = WrapperPetriNet.Transition("t_par2_join", label="+")
    t_par2_join.set_region_type("parallel_join")
    p_par2_end = WrapperPetriNet.Place("p_par2_end")
    
    t_c_exit2 = WrapperPetriNet.Transition("t_c_exit2", label="")
    t_c_exit2.set_region_type("choice_exit")
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add all places
    for p in [p_start, p_par1_start, p_r1, p_r1_end, p_r2, p_r2_end, p_par1_end,
              p_par2_start, p_r3, p_r3_end, p_r4, p_r4_end, p_par2_end, p_end]:
        net.places.add(p)
    
    # Add all transitions
    for t in [t_c_split1, t_c_split2, t_par1_split, t_r1, t_r2, t_par1_join, t_c_exit1,
              t_par2_split, t_r3, t_r4, t_par2_join, t_c_exit2]:
        net.transitions.add(t)
    
    # Arcs - Choice split
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_c_split1))
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_c_split2))
    
    # Branch A arcs
    net.arcs.add(WrapperPetriNet.Arc(t_c_split1, p_par1_start))
    net.arcs.add(WrapperPetriNet.Arc(p_par1_start, t_par1_split))
    net.arcs.add(WrapperPetriNet.Arc(t_par1_split, p_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_par1_split, p_r2))
    net.arcs.add(WrapperPetriNet.Arc(p_r1, t_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_r1, p_r1_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r2, t_r2))
    net.arcs.add(WrapperPetriNet.Arc(t_r2, p_r2_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r1_end, t_par1_join))
    net.arcs.add(WrapperPetriNet.Arc(p_r2_end, t_par1_join))
    net.arcs.add(WrapperPetriNet.Arc(t_par1_join, p_par1_end))
    net.arcs.add(WrapperPetriNet.Arc(p_par1_end, t_c_exit1))
    net.arcs.add(WrapperPetriNet.Arc(t_c_exit1, p_end))
    
    # Branch B arcs
    net.arcs.add(WrapperPetriNet.Arc(t_c_split2, p_par2_start))
    net.arcs.add(WrapperPetriNet.Arc(p_par2_start, t_par2_split))
    net.arcs.add(WrapperPetriNet.Arc(t_par2_split, p_r3))
    net.arcs.add(WrapperPetriNet.Arc(t_par2_split, p_r4))
    net.arcs.add(WrapperPetriNet.Arc(p_r3, t_r3))
    net.arcs.add(WrapperPetriNet.Arc(t_r3, p_r3_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r4, t_r4))
    net.arcs.add(WrapperPetriNet.Arc(t_r4, p_r4_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r3_end, t_par2_join))
    net.arcs.add(WrapperPetriNet.Arc(p_r4_end, t_par2_join))
    net.arcs.add(WrapperPetriNet.Arc(t_par2_join, p_par2_end))
    net.arcs.add(WrapperPetriNet.Arc(p_par2_end, t_c_exit2))
    net.arcs.add(WrapperPetriNet.Arc(t_c_exit2, p_end))
    
    # Region tree
    r1_node = RegionNode('task', 10, 'R1', elements=['t_r1', 'p_r1', 'p_r1_end'])
    r2_node = RegionNode('task', 11, 'R2', elements=['t_r2', 'p_r2', 'p_r2_end'])
    r3_node = RegionNode('task', 12, 'R3', elements=['t_r3', 'p_r3', 'p_r3_end'])
    r4_node = RegionNode('task', 13, 'R4', elements=['t_r4', 'p_r4', 'p_r4_end'])
    
    par1_node = RegionNode('parallel', 3, 'R1 || R2',
                           children=[r1_node, r2_node],
                           elements=['t_par1_split', 't_par1_join', 'p_par1_start', 'p_par1_end'])
    par2_node = RegionNode('parallel', 4, 'R3 || R4',
                           children=[r3_node, r4_node],
                           elements=['t_par2_split', 't_par2_join', 'p_par2_start', 'p_par2_end'])
    
    choice_node = RegionNode('choice', 1, '(R1 || R2) /[C1] (R3 || R4)',
                             children=[par1_node, par2_node],
                             elements=['start', 'end', 't_c_split1', 't_c_exit1', 't_c_split2', 't_c_exit2'])
    
    return net, choice_node


def create_parallel_with_loop():
    """R1 || <R2 [L1]>"""
    net = WrapperPetriNet(name="parallel_with_loop")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t_split = WrapperPetriNet.Transition("t_split", label="+")
    t_split.set_region_type("parallel_split")
    
    # Branch A: Simple task R1
    p_r1 = WrapperPetriNet.Place("p_r1")
    t_r1 = WrapperPetriNet.Transition("t_r1", label="R1")
    t_r1.set_region_type("task")
    t_r1.duration = 2.0
    p_r1_end = WrapperPetriNet.Place("p_r1_end")
    
    # Branch B: Loop <R2 [L1]>
    p_loop_start = WrapperPetriNet.Place("p_loop_start")
    t_loop_entry = WrapperPetriNet.Transition("t_loop_entry", label="")
    t_loop_entry.set_region_type("loop_entry")
    
    p_r2 = WrapperPetriNet.Place("p_r2")
    t_r2 = WrapperPetriNet.Transition("t_r2", label="R2")
    t_r2.set_region_type("task")
    t_r2.duration = 1.5
    p_r2_end = WrapperPetriNet.Place("p_r2_end")
    
    t_loop_back = WrapperPetriNet.Transition("t_loop_back", label="0.3")
    t_loop_back.set_region_type("loop_up")
    t_loop_back.set_probability(0.3)
    
    t_loop_exit = WrapperPetriNet.Transition("t_loop_exit", label="0.7")
    t_loop_exit.set_region_type("loop")
    t_loop_exit.set_probability(0.7)
    
    p_loop_end = WrapperPetriNet.Place("p_loop_end")
    
    t_join = WrapperPetriNet.Transition("t_join", label="+")
    t_join.set_region_type("parallel_join")
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add places and transitions
    for p in [p_start, p_r1, p_r1_end, p_loop_start, p_r2, p_r2_end, p_loop_end, p_end]:
        net.places.add(p)
    for t in [t_split, t_r1, t_loop_entry, t_r2, t_loop_back, t_loop_exit, t_join]:
        net.transitions.add(t)
    
    # Arcs
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_loop_start))
    net.arcs.add(WrapperPetriNet.Arc(p_r1, t_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_r1, p_r1_end))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_start, t_loop_entry))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_entry, p_r2))
    net.arcs.add(WrapperPetriNet.Arc(p_r2, t_r2))
    net.arcs.add(WrapperPetriNet.Arc(t_r2, p_r2_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r2_end, t_loop_back))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_back, p_r2))
    net.arcs.add(WrapperPetriNet.Arc(p_r2_end, t_loop_exit))
    net.arcs.add(WrapperPetriNet.Arc(t_loop_exit, p_loop_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r1_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_loop_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))
    
    # Region tree
    r1_node = RegionNode('task', 3, 'R1', elements=['t_r1', 'p_r1', 'p_r1_end'])
    r2_node = RegionNode('task', 5, 'R2', elements=['t_r2', 'p_r2', 'p_r2_end'])
    
    loop_node = RegionNode('loop', 4, '<R2 [L1]>',
                           children=[r2_node],
                           elements=['t_loop_entry', 't_loop_back', 't_loop_exit', 'p_loop_start', 'p_loop_end'])
    
    parallel_node = RegionNode('parallel', 1, 'R1 || <R2 [L1]>',
                               children=[r1_node, loop_node],
                               elements=['t_split', 't_join', 'start', 'end'])
    
    return net, parallel_node


def create_sequential_in_parallel():
    """(R1, R2) || (R3, R4)"""
    net = WrapperPetriNet(name="sequential_in_parallel")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    t_split = WrapperPetriNet.Transition("t_split", label="+")
    t_split.set_region_type("parallel_split")
    
    # Branch A: Sequence R1, R2
    p_r1 = WrapperPetriNet.Place("p_r1")
    t_r1 = WrapperPetriNet.Transition("t_r1", label="R1")
    t_r1.set_region_type("task")
    t_r1.duration = 2.0
    p_r1_end = WrapperPetriNet.Place("p_r1_end")
    
    t_r2 = WrapperPetriNet.Transition("t_r2", label="R2")
    t_r2.set_region_type("task")
    t_r2.duration = 1.5
    p_r2_end = WrapperPetriNet.Place("p_r2_end")
    
    # Branch B: Sequence R3, R4
    p_r3 = WrapperPetriNet.Place("p_r3")
    t_r3 = WrapperPetriNet.Transition("t_r3", label="R3")
    t_r3.set_region_type("task")
    t_r3.duration = 3.0
    p_r3_end = WrapperPetriNet.Place("p_r3_end")
    
    t_r4 = WrapperPetriNet.Transition("t_r4", label="R4")
    t_r4.set_region_type("task")
    t_r4.duration = 2.5
    p_r4_end = WrapperPetriNet.Place("p_r4_end")
    
    t_join = WrapperPetriNet.Transition("t_join", label="+")
    t_join.set_region_type("parallel_join")
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add places and transitions
    for p in [p_start, p_r1, p_r1_end, p_r2_end, p_r3, p_r3_end, p_r4_end, p_end]:
        net.places.add(p)
    for t in [t_split, t_r1, t_r2, t_r3, t_r4, t_join]:
        net.transitions.add(t)
    
    # Arcs
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_split, p_r3))
    # Branch A
    net.arcs.add(WrapperPetriNet.Arc(p_r1, t_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_r1, p_r1_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r1_end, t_r2))
    net.arcs.add(WrapperPetriNet.Arc(t_r2, p_r2_end))
    # Branch B
    net.arcs.add(WrapperPetriNet.Arc(p_r3, t_r3))
    net.arcs.add(WrapperPetriNet.Arc(t_r3, p_r3_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r3_end, t_r4))
    net.arcs.add(WrapperPetriNet.Arc(t_r4, p_r4_end))
    # Join
    net.arcs.add(WrapperPetriNet.Arc(p_r2_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(p_r4_end, t_join))
    net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))
    
    # Region tree
    r1_node = RegionNode('task', 3, 'R1', elements=['t_r1', 'p_r1', 'p_r1_end'])
    r2_node = RegionNode('task', 4, 'R2', elements=['t_r2', 'p_r1_end', 'p_r2_end'])
    r3_node = RegionNode('task', 5, 'R3', elements=['t_r3', 'p_r3', 'p_r3_end'])
    r4_node = RegionNode('task', 6, 'R4', elements=['t_r4', 'p_r3_end', 'p_r4_end'])
    
    seq1_node = RegionNode('sequential', 2, 'R1, R2',
                           children=[r1_node, r2_node])
    seq2_node = RegionNode('sequential', 2, 'R3, R4',
                           children=[r3_node, r4_node])
    
    parallel_node = RegionNode('parallel', 1, '(R1, R2) || (R3, R4)',
                               children=[seq1_node, seq2_node],
                               elements=['t_split', 't_join', 'start', 'end'])
    
    return net, parallel_node


def create_nested_choice():
    """(R1 /[C1] R2) /[C2] R3"""
    net = WrapperPetriNet(name="nested_choice")
    
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id"
    
    # Outer choice split
    t_outer_split1 = WrapperPetriNet.Transition("t_outer_split1", label="")
    t_outer_split1.set_region_type("choice")
    t_outer_split2 = WrapperPetriNet.Transition("t_outer_split2", label="")
    t_outer_split2.set_region_type("choice")
    
    # Branch A: Inner choice (R1 /[C1] R2)
    p_inner_start = WrapperPetriNet.Place("p_inner_start")
    
    t_inner_split1 = WrapperPetriNet.Transition("t_inner_split1", label="")
    t_inner_split1.set_region_type("choice")
    t_inner_split2 = WrapperPetriNet.Transition("t_inner_split2", label="")
    t_inner_split2.set_region_type("choice")
    
    p_r1 = WrapperPetriNet.Place("p_r1")
    t_r1 = WrapperPetriNet.Transition("t_r1", label="R1")
    t_r1.set_region_type("task")
    t_r1.duration = 2.0
    p_r1_end = WrapperPetriNet.Place("p_r1_end")
    t_inner_exit1 = WrapperPetriNet.Transition("t_inner_exit1", label="")
    t_inner_exit1.set_region_type("choice_exit")
    
    p_r2 = WrapperPetriNet.Place("p_r2")
    t_r2 = WrapperPetriNet.Transition("t_r2", label="R2")
    t_r2.set_region_type("task")
    t_r2.duration = 1.5
    p_r2_end = WrapperPetriNet.Place("p_r2_end")
    t_inner_exit2 = WrapperPetriNet.Transition("t_inner_exit2", label="")
    t_inner_exit2.set_region_type("choice_exit")
    
    p_inner_end = WrapperPetriNet.Place("p_inner_end")
    t_outer_exit1 = WrapperPetriNet.Transition("t_outer_exit1", label="")
    t_outer_exit1.set_region_type("choice_exit")
    
    # Branch B: Simple task R3
    p_r3 = WrapperPetriNet.Place("p_r3")
    t_r3 = WrapperPetriNet.Transition("t_r3", label="R3")
    t_r3.set_region_type("task")
    t_r3.duration = 3.0
    p_r3_end = WrapperPetriNet.Place("p_r3_end")
    t_outer_exit2 = WrapperPetriNet.Transition("t_outer_exit2", label="")
    t_outer_exit2.set_region_type("choice_exit")
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id"
    
    # Add places and transitions
    for p in [p_start, p_inner_start, p_r1, p_r1_end, p_r2, p_r2_end, p_inner_end, p_r3, p_r3_end, p_end]:
        net.places.add(p)
    for t in [t_outer_split1, t_outer_split2, t_inner_split1, t_inner_split2,
              t_r1, t_r2, t_r3, t_inner_exit1, t_inner_exit2, t_outer_exit1, t_outer_exit2]:
        net.transitions.add(t)
    
    # Arcs - Outer choice
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_outer_split1))
    net.arcs.add(WrapperPetriNet.Arc(p_start, t_outer_split2))
    
    # Branch A: Inner choice
    net.arcs.add(WrapperPetriNet.Arc(t_outer_split1, p_inner_start))
    net.arcs.add(WrapperPetriNet.Arc(p_inner_start, t_inner_split1))
    net.arcs.add(WrapperPetriNet.Arc(p_inner_start, t_inner_split2))
    # R1 path
    net.arcs.add(WrapperPetriNet.Arc(t_inner_split1, p_r1))
    net.arcs.add(WrapperPetriNet.Arc(p_r1, t_r1))
    net.arcs.add(WrapperPetriNet.Arc(t_r1, p_r1_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r1_end, t_inner_exit1))
    net.arcs.add(WrapperPetriNet.Arc(t_inner_exit1, p_inner_end))
    # R2 path
    net.arcs.add(WrapperPetriNet.Arc(t_inner_split2, p_r2))
    net.arcs.add(WrapperPetriNet.Arc(p_r2, t_r2))
    net.arcs.add(WrapperPetriNet.Arc(t_r2, p_r2_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r2_end, t_inner_exit2))
    net.arcs.add(WrapperPetriNet.Arc(t_inner_exit2, p_inner_end))
    # Inner end -> Outer exit
    net.arcs.add(WrapperPetriNet.Arc(p_inner_end, t_outer_exit1))
    net.arcs.add(WrapperPetriNet.Arc(t_outer_exit1, p_end))
    
    # Branch B: R3
    net.arcs.add(WrapperPetriNet.Arc(t_outer_split2, p_r3))
    net.arcs.add(WrapperPetriNet.Arc(p_r3, t_r3))
    net.arcs.add(WrapperPetriNet.Arc(t_r3, p_r3_end))
    net.arcs.add(WrapperPetriNet.Arc(p_r3_end, t_outer_exit2))
    net.arcs.add(WrapperPetriNet.Arc(t_outer_exit2, p_end))
    
    # Region tree
    r1_node = RegionNode('task', 5, 'R1', elements=['t_r1', 'p_r1', 'p_r1_end'])
    r2_node = RegionNode('task', 6, 'R2', elements=['t_r2', 'p_r2', 'p_r2_end'])
    r3_node = RegionNode('task', 4, 'R3', elements=['t_r3', 'p_r3', 'p_r3_end'])
    
    inner_choice = RegionNode('choice', 3, 'R1 /[C1] R2',
                              children=[r1_node, r2_node],
                              elements=['p_inner_start', 'p_inner_end',
                                        't_inner_split1', 't_inner_exit1',
                                        't_inner_split2', 't_inner_exit2'])
    
    outer_choice = RegionNode('choice', 1, '(R1 /[C1] R2) /[C2] R3',
                              children=[inner_choice, r3_node],
                              elements=['start', 'end',
                                        't_outer_split1', 't_outer_exit1',
                                        't_outer_split2', 't_outer_exit2'])
    
    return net, outer_choice


if __name__ == "__main__":
    output_dir = "docs/verification_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # =========================================================================
    # SINGLE PATTERNS
    # =========================================================================
    
    print("Generating single task...")
    net1 = create_single_task()
    svg1 = petri_net_to_svg(net1, width=800, height=200)
    save_svg(svg1, f"{output_dir}/svg_single_task.svg")
    print(f"  Saved to {output_dir}/svg_single_task.svg")
    
    print("Generating two tasks sequence...")
    net2 = create_sequence_two_tasks()
    svg2 = petri_net_to_svg(net2, width=800, height=200)
    save_svg(svg2, f"{output_dir}/svg_sequence_two.svg")
    print(f"  Saved to {output_dir}/svg_sequence_two.svg")
    
    print("Generating choice pattern...")
    net3 = create_choice()
    svg3 = petri_net_to_svg(net3, width=800, height=400)
    save_svg(svg3, f"{output_dir}/svg_choice.svg")
    print(f"  Saved to {output_dir}/svg_choice.svg")
    
    print("Generating parallel pattern...")
    net4 = create_parallel()
    svg4 = petri_net_to_svg(net4, width=800, height=400)
    save_svg(svg4, f"{output_dir}/svg_parallel.svg")
    print(f"  Saved to {output_dir}/svg_parallel.svg")
    
    print("Generating simple parallel choice ((R2 /[C1] R3) || R4)...")
    net12, tree12 = create_parallel_choice_simple()
    svg12 = petri_net_to_svg(net12, width=800, height=400, region_tree=tree12)
    save_svg(svg12, f"{output_dir}/svg_parallel_choice_simple_v2.svg")
    print(f"  Saved to {output_dir}/svg_parallel_choice_simple_v2.svg")
    
    print("Generating simple parallel choice ((R2 /[C1] R3) || R4)...")
    net12, tree12 = create_parallel_choice_simple()
    svg12 = petri_net_to_svg(net12, width=800, height=400, region_tree=tree12)
    save_svg(svg12, f"{output_dir}/svg_parallel_choice_simple_v2.svg")
    print(f"  Saved to {output_dir}/svg_parallel_choice_simple_v2.svg")

    print("Generating simple parallel choice ((R2 /[C1] R3) || R4)...")
    net12, tree12 = create_parallel_choice_simple()
    svg12 = petri_net_to_svg(net12, width=800, height=400, region_tree=tree12)
    save_svg(svg12, f"{output_dir}/svg_parallel_choice_simple_v2.svg")
    print(f"  Saved to {output_dir}/svg_parallel_choice_simple_v2.svg")
    
    print("Generating loop pattern...")
    net5 = create_loop()
    svg5 = petri_net_to_svg(net5, width=800, height=300)
    save_svg(svg5, f"{output_dir}/svg_loop.svg")
    print(f"  Saved to {output_dir}/svg_loop.svg")
    
    print("Generating nature pattern...")
    net6 = create_nature()
    svg6 = petri_net_to_svg(net6, width=800, height=400)
    save_svg(svg6, f"{output_dir}/svg_nature.svg")
    print(f"  Saved to {output_dir}/svg_nature.svg")
    
    # =========================================================================
    # COMBINATION PATTERNS
    # =========================================================================
    
    # Combination 1: Sequential with Parallel
    print("Generating combo: Sequential + Parallel...")
    net_combo1, tree_combo1 = create_sequential_parallel()
    svg_combo1 = petri_net_to_svg(net_combo1, width=1200, height=500, region_tree=tree_combo1)
    save_svg(svg_combo1, f"{output_dir}/svg_sequential_parallel.svg")
    print(f"  Saved to {output_dir}/svg_sequential_parallel.svg")
    
    # Combination 2: Sequential with Choice
    print("Generating combo: Sequential + Choice...")
    net_combo2, tree_combo2 = create_sequential_choice()
    svg_combo2 = petri_net_to_svg(net_combo2, width=1200, height=500, region_tree=tree_combo2)
    save_svg(svg_combo2, f"{output_dir}/svg_sequential_choice.svg")
    print(f"  Saved to {output_dir}/svg_sequential_choice.svg")
    
    # Combination 3: Sequential with Loop
    print("Generating combo: Sequential + Loop...")
    net_combo3, tree_combo3 = create_sequential_loop()
    svg_combo3 = petri_net_to_svg(net_combo3, width=1200, height=400, region_tree=tree_combo3)
    save_svg(svg_combo3, f"{output_dir}/svg_sequential_loop.svg")
    print(f"  Saved to {output_dir}/svg_sequential_loop.svg")
    
    # Combination 4: Sequential with Nature
    print("Generating combo: Sequential + Nature...")
    net_combo4, tree_combo4 = create_sequential_nature()
    svg_combo4 = petri_net_to_svg(net_combo4, width=1200, height=500, region_tree=tree_combo4)
    save_svg(svg_combo4, f"{output_dir}/svg_sequential_nature.svg")
    print(f"  Saved to {output_dir}/svg_sequential_nature.svg")
    
    # Combination 5: Complex Parallel
    print("Generating combo: Complex Parallel...")
    net_complex, tree_complex = create_complex_parallel()
    svg_complex = petri_net_to_svg(net_complex, width=1200, height=600, region_tree=tree_complex)
    save_svg(svg_complex, f"{output_dir}/svg_complex_parallel.svg")
    print(f"  Saved to {output_dir}/svg_complex_parallel.svg")
    
    # =========================================================================
    # NEW ADVANCED COMBINATIONS
    # =========================================================================
    
    # Advanced 1: Choice of Parallels - (R1 || R2) /[C1] (R3 || R4)
    print("Generating advanced: Choice of Parallels...")
    net_adv1, tree_adv1 = create_choice_of_parallels()
    svg_adv1 = petri_net_to_svg(net_adv1, width=1400, height=600, region_tree=tree_adv1)
    save_svg(svg_adv1, f"{output_dir}/svg_choice_of_parallels.svg")
    print(f"  Saved to {output_dir}/svg_choice_of_parallels.svg")
    
    # Advanced 2: Parallel with Loop - (R1 || <R2 [L1]>)
    print("Generating advanced: Parallel with Loop...")
    net_adv2, tree_adv2 = create_parallel_with_loop()
    svg_adv2 = petri_net_to_svg(net_adv2, width=1200, height=500, region_tree=tree_adv2)
    save_svg(svg_adv2, f"{output_dir}/svg_parallel_with_loop.svg")
    print(f"  Saved to {output_dir}/svg_parallel_with_loop.svg")
    
    # Advanced 3: Sequential in Parallel - (R1, R2) || (R3, R4)
    print("Generating advanced: Sequential in Parallel...")
    net_adv3, tree_adv3 = create_sequential_in_parallel()
    svg_adv3 = petri_net_to_svg(net_adv3, width=1400, height=500, region_tree=tree_adv3)
    save_svg(svg_adv3, f"{output_dir}/svg_sequential_in_parallel.svg")
    print(f"  Saved to {output_dir}/svg_sequential_in_parallel.svg")
    
    # Advanced 4: Nested Choice - (R1 /[C1] R2) /[C2] R3
    print("Generating advanced: Nested Choice...")
    net_adv4, tree_adv4 = create_nested_choice()
    svg_adv4 = petri_net_to_svg(net_adv4, width=1200, height=600, region_tree=tree_adv4)
    save_svg(svg_adv4, f"{output_dir}/svg_nested_choice.svg")
    print(f"  Saved to {output_dir}/svg_nested_choice.svg")
    
    print("Done!")

