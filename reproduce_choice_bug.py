import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from model.region import RegionModel, RegionType
from converter.spin import from_region
from svg_viz import spin_to_svg, save_svg

# Define Choice Pattern
def create_choice_pattern():
    task1 = RegionModel(id="1", type=RegionType.TASK, label="T1", duration=2, impacts=[1.0])
    task2 = RegionModel(id="2", type=RegionType.TASK, label="T2", duration=2, impacts=[1.0])
    task3 = RegionModel(id="3", type=RegionType.TASK, label="T3", duration=2, impacts=[1.0])
    
    # Choice with wide/tall branches to trigger vertical heuristic
    choice = RegionModel(
        id="4", 
        type=RegionType.CHOICE, 
        label="C1", 
        children=[task1, task2, task3]
    )
    return choice

if __name__ == "__main__":
    print("Generating Choice Pattern SVG...")
    region = create_choice_pattern()
    net, im, fm = from_region(region)
    
    # Generate SVG
    svg_content = spin_to_svg(net, width=800, height=400, region=region)
    save_svg(svg_content, "debug_choice.svg")
    print("SVG saved to debug_choice.svg")
