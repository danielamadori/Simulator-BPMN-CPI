
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from dot import petri_net_to_dot
from model.petri_net.wrapper import WrapperPetriNet
import graphviz

def create_sample_net(name):
    net = WrapperPetriNet(name=name)
    
    # Create Places
    p_start = WrapperPetriNet.Place("start")
    p_start.entry_id = "start_id" # mimic entry place behavior
    
    p_end = WrapperPetriNet.Place("end")
    p_end.exit_id = "end_id" # mimic exit place behavior

    net.places.add(p_start)
    net.places.add(p_end)

    if name == "sequence":
        # Option 2 style: Nested clusters with shared places between inner regions
        # R1 and R2 are inner regions, shared place is outside both but arcs connect them
        
        t1 = WrapperPetriNet.Transition("t1", label="R1")
        t1.set_region_type("task")
        t1.set_region_label("R1")  # Inside R1 cluster
        
        p1 = WrapperPetriNet.Place("p1")  # Shared place - NO region_label (outside inner clusters)
        
        t2 = WrapperPetriNet.Transition("t2", label="R2")
        t2.set_region_type("task")
        t2.set_region_label("R2")  # Inside R2 cluster
        
        net.places.add(p1)
        net.transitions.add(t1)
        net.transitions.add(t2)
        
        net.arcs.add(WrapperPetriNet.Arc(p_start, t1))
        net.arcs.add(WrapperPetriNet.Arc(t1, p1))
        net.arcs.add(WrapperPetriNet.Arc(p1, t2))
        net.arcs.add(WrapperPetriNet.Arc(t2, p_end))
        
    elif name == "choice":
        # Structure matching reference image:
        # Start -> Split -> [Branch A: Entry_A -> Task_A -> Exit_A] -> Join -> End
        #               -> [Branch B: Entry_B -> Task_B -> Exit_B] ->
        
        # Split (probabilistic, white with border)
        t_split = WrapperPetriNet.Transition("split", label="")
        t_split.set_region_type("choice")
        t_split.set_probability(None) # Not probabilistic for split itself
        
        # Branch A: Place -> Entry_A -> Place -> Task_A -> Place -> Exit_A -> Place
        p_after_split_a = WrapperPetriNet.Place("p_after_split_a")
        
        t_entry_a = WrapperPetriNet.Transition("entry_a", label="")
        t_entry_a.set_region_type("choice")
        t_entry_a.set_probability(0.6)  # Probabilistic entry
        
        p_before_task_a = WrapperPetriNet.Place("p_before_task_a")
        
        t_task_a = WrapperPetriNet.Transition("task_a", label="R1")
        t_task_a.set_region_type("task")
        t_task_a.set_region_label("R1")
        
        p_after_task_a = WrapperPetriNet.Place("p_after_task_a")
        
        t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
        t_exit_a.set_region_type("choice")
        # Exit is not probabilistic
        
        p_before_join_a = WrapperPetriNet.Place("p_before_join_a")
        
        # Branch B: Place -> Entry_B -> Place -> Task_B -> Place -> Exit_B -> Place
        p_after_split_b = WrapperPetriNet.Place("p_after_split_b")
        
        t_entry_b = WrapperPetriNet.Transition("entry_b", label="")
        t_entry_b.set_region_type("choice")
        t_entry_b.set_probability(0.4)  # Probabilistic entry
        
        p_before_task_b = WrapperPetriNet.Place("p_before_task_b")
        
        t_task_b = WrapperPetriNet.Transition("task_b", label="R2")
        t_task_b.set_region_type("task")
        t_task_b.set_region_label("R2")
        
        p_after_task_b = WrapperPetriNet.Place("p_after_task_b")
        
        t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
        t_exit_b.set_region_type("choice")
        # Exit is not probabilistic
        
        p_before_join_b = WrapperPetriNet.Place("p_before_join_b")
        
        # Join
        t_join = WrapperPetriNet.Transition("join", label="")
        t_join.set_region_type("choice")
        # Join is not probabilistic
        
        # Add to net
        net.places.add(p_after_split_a)
        net.places.add(p_before_task_a)
        net.places.add(p_after_task_a)
        net.places.add(p_before_join_a)
        net.places.add(p_after_split_b)
        net.places.add(p_before_task_b)
        net.places.add(p_after_task_b)
        net.places.add(p_before_join_b)
        
        net.transitions.add(t_split)
        net.transitions.add(t_entry_a)
        net.transitions.add(t_task_a)
        net.transitions.add(t_exit_a)
        net.transitions.add(t_entry_b)
        net.transitions.add(t_task_b)
        net.transitions.add(t_exit_b)
        net.transitions.add(t_join)
        
        # Arcs
        # Start -> Split
        net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
        
        # Split -> Branch A
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_after_split_a))
        net.arcs.add(WrapperPetriNet.Arc(p_after_split_a, t_entry_a))
        net.arcs.add(WrapperPetriNet.Arc(t_entry_a, p_before_task_a))
        net.arcs.add(WrapperPetriNet.Arc(p_before_task_a, t_task_a))
        net.arcs.add(WrapperPetriNet.Arc(t_task_a, p_after_task_a))
        net.arcs.add(WrapperPetriNet.Arc(p_after_task_a, t_exit_a))
        net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p_before_join_a))
        
        # Split -> Branch B
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_after_split_b))
        net.arcs.add(WrapperPetriNet.Arc(p_after_split_b, t_entry_b))
        net.arcs.add(WrapperPetriNet.Arc(t_entry_b, p_before_task_b))
        net.arcs.add(WrapperPetriNet.Arc(p_before_task_b, t_task_b))
        net.arcs.add(WrapperPetriNet.Arc(t_task_b, p_after_task_b))
        net.arcs.add(WrapperPetriNet.Arc(p_after_task_b, t_exit_b))
        net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p_before_join_b))
        
        # Branches -> Join
        net.arcs.add(WrapperPetriNet.Arc(p_before_join_a, t_join))
        net.arcs.add(WrapperPetriNet.Arc(p_before_join_b, t_join))
        
        # Join -> End
        net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))

    elif name == "parallel":
        # Start -> T_split -> {P_a, P_b} -> {Ta, Tb} -> {P_c, P_d} -> T_join -> End
        
        t_split = WrapperPetriNet.Transition("split", label="+")
        t_split.set_region_type("parallel")
        t_split.set_probability(1.0)
        
        p_a = WrapperPetriNet.Place("p_a")
        t_a = WrapperPetriNet.Transition("t_a", label="R1")
        t_a.set_region_type("task")
        t_a.set_region_label("R1")
        p_a_end = WrapperPetriNet.Place("p_a_end")
        
        p_b = WrapperPetriNet.Place("p_b")
        t_b = WrapperPetriNet.Transition("t_b", label="R2")
        t_b.set_region_type("task")
        t_b.set_region_label("R2")
        p_b_end = WrapperPetriNet.Place("p_b_end")
        
        t_join = WrapperPetriNet.Transition("join", label="+")
        t_join.set_region_type("parallel")
        t_join.set_probability(1.0)
        
        net.transitions.add(t_split)
        net.transitions.add(t_a)
        net.transitions.add(t_b)
        net.transitions.add(t_join)
        
        net.places.add(p_a)
        net.places.add(p_b)
        net.places.add(p_a_end)
        net.places.add(p_b_end)
        
        # Split (1 -> 2)
        net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_a))
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_b))
        
        # Branches
        net.arcs.add(WrapperPetriNet.Arc(p_a, t_a))
        net.arcs.add(WrapperPetriNet.Arc(t_a, p_a_end))
        net.arcs.add(WrapperPetriNet.Arc(p_b, t_b))
        net.arcs.add(WrapperPetriNet.Arc(t_b, p_b_end))
        
        # Join (2 -> 1)
        net.arcs.add(WrapperPetriNet.Arc(p_a_end, t_join))
        net.arcs.add(WrapperPetriNet.Arc(p_b_end, t_join))
        net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))

    elif name == "loop":
        # Start -> Entry -> Child_Entry -> Task -> Child_Exit -> Loop -> Child_Entry
        #                                                     -> Exit -> End
        
        t_entry = WrapperPetriNet.Transition("entry", label="Entry")
        t_entry.set_region_type("loop")
        t_entry.set_probability(1.0)
        
        p_child_entry = WrapperPetriNet.Place("p_child_entry")
        t_task = WrapperPetriNet.Transition("task", label="R1")
        t_task.set_region_type("task")
        t_task.set_region_label("R1")
        p_child_exit = WrapperPetriNet.Place("p_child_exit")
        
        t_loop = WrapperPetriNet.Transition("loop", label="Loop")
        t_loop.set_region_type("loop")
        t_loop.set_probability(0.8) # Probabilistic
        
        t_exit = WrapperPetriNet.Transition("exit", label="Exit")
        t_exit.set_region_type("loop")
        t_exit.set_probability(0.2) # Probabilistic
        
        net.transitions.add(t_entry)
        net.transitions.add(t_task)
        net.transitions.add(t_loop)
        net.transitions.add(t_exit)
        
        net.places.add(p_child_entry)
        net.places.add(p_child_exit)
        
        # Entry
        net.arcs.add(WrapperPetriNet.Arc(p_start, t_entry))
        net.arcs.add(WrapperPetriNet.Arc(t_entry, p_child_entry))
        
        # Task
        net.arcs.add(WrapperPetriNet.Arc(p_child_entry, t_task))
        net.arcs.add(WrapperPetriNet.Arc(t_task, p_child_exit))
        
        # Loop Back
        net.arcs.add(WrapperPetriNet.Arc(p_child_exit, t_loop))
        net.arcs.add(WrapperPetriNet.Arc(t_loop, p_child_entry))
        
        # Exit Loop
        net.arcs.add(WrapperPetriNet.Arc(p_child_exit, t_exit))
        net.arcs.add(WrapperPetriNet.Arc(t_exit, p_end))

    elif name == "nature":
        # Same structure as choice but with region_type='nature' for green colors
        # Start -> Split -> [Branch A: Entry_A -> Task_A -> Exit_A] -> Join -> End
        #               -> [Branch B: Entry_B -> Task_B -> Exit_B] ->
        
        # Split
        t_split = WrapperPetriNet.Transition("split", label="")
        t_split.set_region_type("nature")
        t_split.set_probability(None)
        
        # Branch A
        p_after_split_a = WrapperPetriNet.Place("p_after_split_a")
        
        t_entry_a = WrapperPetriNet.Transition("entry_a", label="")
        t_entry_a.set_region_type("nature")
        t_entry_a.set_probability(0.7)  # Probabilistic entry (π)
        
        p_before_task_a = WrapperPetriNet.Place("p_before_task_a")
        
        t_task_a = WrapperPetriNet.Transition("task_a", label="R1")
        t_task_a.set_region_type("task")
        t_task_a.set_region_label("R1")
        
        p_after_task_a = WrapperPetriNet.Place("p_after_task_a")
        
        t_exit_a = WrapperPetriNet.Transition("exit_a", label="")
        t_exit_a.set_region_type("nature")
        
        p_before_join_a = WrapperPetriNet.Place("p_before_join_a")
        
        # Branch B
        p_after_split_b = WrapperPetriNet.Place("p_after_split_b")
        
        t_entry_b = WrapperPetriNet.Transition("entry_b", label="")
        t_entry_b.set_region_type("nature")
        t_entry_b.set_probability(0.3)  # Probabilistic entry (1-π)
        
        p_before_task_b = WrapperPetriNet.Place("p_before_task_b")
        
        t_task_b = WrapperPetriNet.Transition("task_b", label="R2")
        t_task_b.set_region_type("task")
        t_task_b.set_region_label("R2")
        
        p_after_task_b = WrapperPetriNet.Place("p_after_task_b")
        
        t_exit_b = WrapperPetriNet.Transition("exit_b", label="")
        t_exit_b.set_region_type("nature")
        
        p_before_join_b = WrapperPetriNet.Place("p_before_join_b")
        
        # Join
        t_join = WrapperPetriNet.Transition("join", label="")
        t_join.set_region_type("nature")
        
        # Add to net
        net.places.add(p_after_split_a)
        net.places.add(p_before_task_a)
        net.places.add(p_after_task_a)
        net.places.add(p_before_join_a)
        net.places.add(p_after_split_b)
        net.places.add(p_before_task_b)
        net.places.add(p_after_task_b)
        net.places.add(p_before_join_b)
        
        net.transitions.add(t_split)
        net.transitions.add(t_entry_a)
        net.transitions.add(t_task_a)
        net.transitions.add(t_exit_a)
        net.transitions.add(t_entry_b)
        net.transitions.add(t_task_b)
        net.transitions.add(t_exit_b)
        net.transitions.add(t_join)
        
        # Arcs
        net.arcs.add(WrapperPetriNet.Arc(p_start, t_split))
        
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_after_split_a))
        net.arcs.add(WrapperPetriNet.Arc(p_after_split_a, t_entry_a))
        net.arcs.add(WrapperPetriNet.Arc(t_entry_a, p_before_task_a))
        net.arcs.add(WrapperPetriNet.Arc(p_before_task_a, t_task_a))
        net.arcs.add(WrapperPetriNet.Arc(t_task_a, p_after_task_a))
        net.arcs.add(WrapperPetriNet.Arc(p_after_task_a, t_exit_a))
        net.arcs.add(WrapperPetriNet.Arc(t_exit_a, p_before_join_a))
        
        net.arcs.add(WrapperPetriNet.Arc(t_split, p_after_split_b))
        net.arcs.add(WrapperPetriNet.Arc(p_after_split_b, t_entry_b))
        net.arcs.add(WrapperPetriNet.Arc(t_entry_b, p_before_task_b))
        net.arcs.add(WrapperPetriNet.Arc(p_before_task_b, t_task_b))
        net.arcs.add(WrapperPetriNet.Arc(t_task_b, p_after_task_b))
        net.arcs.add(WrapperPetriNet.Arc(p_after_task_b, t_exit_b))
        net.arcs.add(WrapperPetriNet.Arc(t_exit_b, p_before_join_b))
        
        net.arcs.add(WrapperPetriNet.Arc(p_before_join_a, t_join))
        net.arcs.add(WrapperPetriNet.Arc(p_before_join_b, t_join))
        
        net.arcs.add(WrapperPetriNet.Arc(t_join, p_end))

    return net

def generate_images():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../docs/verification_images'))
    os.makedirs(output_dir, exist_ok=True)
    
    samples = ["sequence", "choice", "parallel", "loop", "nature"]
    
    generated_files = []
    
    for name in samples:
        print(f"Generating {name}...")
        net = create_sample_net(name)
        dot_code = petri_net_to_dot(net)
        
        # Save DOT
        dot_path = os.path.join(output_dir, f"{name}.dot")
        with open(dot_path, "w", encoding='utf-8') as f:
            f.write(dot_code)
            
        # Render PNG
        try:
            s = graphviz.Source(dot_code, filename=name, directory=output_dir, format="png")
            png_path = s.render()
            print(f"  Saved to {png_path}")
            generated_files.append(png_path)
        except Exception as e:
            print(f"  Error rendering {name}: {e}")
            print("  Make sure graphviz is installed/in PATH.")
            # Fallback: Just keep DOT
            generated_files.append(dot_path)

    return generated_files

if __name__ == "__main__":
    files = generate_images()
    print("DONE. Files:", files)
