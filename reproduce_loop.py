import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from model.region import RegionModel, RegionType
from converter.spin import from_region
from svg_viz import spin_to_svg, save_svg

# Define Loop Pattern: <R1 [L1]>
# Structure: Loop(Task)
def create_loop_pattern():
    # Inner Task
    task = RegionModel(id="1", type=RegionType.TASK, label="T1", duration=2, impacts=[1.5])
    
    # Loop Wrapper
    loop = RegionModel(
        id="2", 
        type=RegionType.LOOP, 
        label="L1", 
        children=[task],
        distribution=0.8,
        bound=3
    )
    return loop

if __name__ == "__main__":
    print("Generating Loop Pattern SVG...")
    region = create_loop_pattern()
    net, im, fm = from_region(region)
    
    # Generate SVG
    svg_content = spin_to_svg(net, width=800, height=400, region=region)
    save_svg(svg_content, "debug_loop.svg")
    print("SVG saved to debug_loop.svg")
