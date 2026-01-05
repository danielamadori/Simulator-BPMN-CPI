import pytest
import sys
import os

# Ensure src is in path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from generate_json_test_nb import get_patterns
from model.region import RegionModel
from converter.spin import from_region

from spin_visualizzation import spin_to_svg

# Get all patterns
patterns = get_patterns()

@pytest.mark.parametrize("pattern", patterns, ids=[p['name'] for p in patterns])
def test_pattern_svg_generation(pattern):
    """
    Tests that a pattern can be successfully converted to a valid SVG visualization.
    Pipeline: JSON -> RegionModel -> Petri Net -> SVG
    """
    print(f"Testing pattern: {pattern['name']}")
    
    # 1. Validate JSON against RegionModel
    region_json = pattern['json']
    region_model = RegionModel.model_validate(region_json)
    
    # 2. Convert to Petri Net
    net, im, fm = from_region(region_model)
    assert net is not None
    
    # 3. Generate SVG
    # using standard dimensions from the notebook
    svg_content = spin_to_svg(net, width=1000, height=500, region=region_model)
    
    # 4. Verify SVG Content
    try:
        assert isinstance(svg_content, str), "SVG generation did not return a string"
        assert svg_content.strip().startswith("<svg"), "Output does not look like an SVG"
        assert "</svg>" in svg_content, "SVG is not properly closed"
        
        # Check for layout errors (NaN values in coordinates)
        # Filter out 'dominant-baseline' which contains 'nan'
        content_lower = svg_content.lower()
        if "nan" in content_lower:
             # Check if it's only dominant-baseline
             clean_content = content_lower.replace("dominant-baseline", "")
             if "nan" in clean_content:
                 print(f"DEBUG: NaN found in pattern {pattern['name']}")
                 for i, line in enumerate(svg_content.splitlines()):
                     if "nan" in line.lower() and "dominant-baseline" not in line.lower():
                         print(f"Line {i+1}: {line.strip()}")
                         
                 assert False, "SVG contains NaN values (excluding dominant-baseline)"
        
        assert "infinity" not in content_lower, "SVG contains Infinity values, indicating layout failure"
        
        # --- Save Artifacts ---
        import os
        import json
        
        # Define output directory
        base_dir = os.path.dirname(__file__)
        output_dir = os.path.join(base_dir, "output")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Sanitize filename
        safe_name = pattern['name'].lower().replace(" ", "_").replace("+", "plus").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
        
        # Save BPMN (JSON)
        bpmn_path = os.path.join(output_dir, f"{safe_name}.json")
        with open(bpmn_path, "w", encoding="utf-8") as f:
            json.dump(pattern['json'], f, indent=2)
            
        # Save SPIN (SVG)
        spin_path = os.path.join(output_dir, f"{safe_name}.svg")
        with open(spin_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
    except AssertionError as e:
        with open("debug_failure.svg", "w", encoding="utf-8") as f:
            # Write the ORIGINAL content, not lowercased
            f.write(svg_content)
        print(f"SVG Content saved to debug_failure.svg")
        raise e
