import json
import re
import os

# Path to the test file
TEST_FILE = r"C:\Users\danie\Projects\GitHub\Simulator-CPI\tests\test_svg_patterns.py"
OUTPUT_NB = r"C:\Users\danie\Projects\GitHub\Simulator-CPI\src\svg_test_suite.ipynb"

def parse_functions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find all functions starting with create_
    # We capture the full function body assuming indentation logic (simplified)
    # Actually, simplistic parsing: read lines, keep state.
    
    functions = {}
    current_func = None
    current_code = []
    
    lines = content.splitlines()
    for line in lines:
        if line.strip().startswith("def create_"):
            if current_func:
                functions[current_func] = "\n".join(current_code)
            current_func = line.split("(")[0].replace("def ", "").strip()
            current_code = [line]
        elif current_func:
            # If line is empty or indented or starts with #, assume part of function
            # If line starts with non-indented text (and not def/class), it might end function.
            # In python structure, top level defs are not indented.
            if line.strip() and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                 # End of function
                 functions[current_func] = "\n".join(current_code)
                 current_func = None
                 current_code = []
            else:
                current_code.append(line)
    
    if current_func:
        functions[current_func] = "\n".join(current_code)
        
    return functions

def create_notebook(functions):
    cells = []
    
    # 1. Imports Cell
    imports_code = """
import sys
import os

# Add current directory to path if needed (for helper modules)
sys.path.append(os.getcwd())

from svg_viz import petri_net_to_svg, RegionNode
from model.petri_net.wrapper import WrapperPetriNet
from IPython.display import SVG, display

print("Imports successful!")
"""
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": imports_code.strip().splitlines(keepends=True)
    })

    # 2. Functions Definitions Cell
    all_funcs_code = "\n\n".join(functions.values())
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": all_funcs_code.splitlines(keepends=True)
    })
    
    # 3. Test Cells
    for func_name in functions:
        markdown_source = f"## Pattern: `{func_name}`"
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [markdown_source]
        })
        
        test_code = f"""
print(f"Generating {func_name}...")
res = {func_name}()

if isinstance(res, tuple):
    net, tree = res
else:
    net, tree = res, None

# Adjust dimensions based on complexity (simple vs complex)
width = 1200 if tree else 800
height = 500 if tree else 400

svg_content = petri_net_to_svg(net, width=width, height=height, region_tree=tree)
display(SVG(svg_content))
"""
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": test_code.strip().splitlines(keepends=True)
        })

    # Create Notebook Dictionary
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.13.2"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    
    return notebook

if __name__ == "__main__":
    print(f"Parsing functions from {TEST_FILE}...")
    funcs = parse_functions(TEST_FILE)
    print(f"Found {len(funcs)} functions: {list(funcs.keys())}")
    
    print(f"Generating notebook to {OUTPUT_NB}...")
    nb_data = create_notebook(funcs)
    
    with open(OUTPUT_NB, 'w', encoding='utf-8') as f:
        json.dump(nb_data, f, indent=2)
        
    print("Done!")
