import json
import os

OUTPUT_NB = r"C:\Users\danie\Projects\GitHub\Simulator-CPI\json_patterns_test.ipynb"

# --- JSON Builders (Helper Functions) ---

def _id_gen():
    i = 0
    while True:
        yield str(i)
        i += 1

gen = _id_gen()
def new_id():
    return next(gen)

# Task counter for T1, T2, T3... labels
_task_counter = 0
_parallel_counter = 0
_choice_counter = 0
_nature_counter = 0
_loop_counter = 0

def _next_task_label():
    global _task_counter
    _task_counter += 1
    return f"T{_task_counter}"

def _next_parallel_label():
    global _parallel_counter
    _parallel_counter += 1
    return f"P{_parallel_counter}"

def _next_choice_label():
    global _choice_counter
    _choice_counter += 1
    return f"C{_choice_counter}"

def _next_nature_label():
    global _nature_counter
    _nature_counter += 1
    return f"N{_nature_counter}"

def _next_loop_label():
    global _loop_counter
    _loop_counter += 1
    return f"L{_loop_counter}"

def task(label=None, duration=1.0, impacts=None):
    if impacts is None: impacts = [1.0]
    # If no label provided, auto-generate T1, T2, etc.
    if label is None:
        label = _next_task_label()
    return {
        "id": new_id(),
        "type": "task",
        "label": label,
        "duration": duration,
        "impacts": impacts
    }

def sequential(children):
    return {
        "id": new_id(),
        "type": "sequential",
        "children": children
    }

def parallel(children, label=None):
    if label is None: label = _next_parallel_label()
    return {
        "id": new_id(),
        "type": "parallel",
        "label": label,
        "children": children
    }

def choice(children, max_delay=0.0, label=None):
    if label is None: label = _next_choice_label()
    return {
        "id": new_id(),
        "type": "choice",
        "label": label,
        "children": children,
        "max_delay": max_delay
    }

def nature(children, distribution, label=None):
    if label is None: label = _next_nature_label()
    return {
        "id": new_id(),
        "type": "nature",
        "label": label,
        "children": children,
        "distribution": distribution
    }

def loop(child, label=None, probability=0.5, bound=5):
    if label is None: label = _next_loop_label()
    return {
        "id": new_id(),
        "type": "loop",
        "label": label,
        "children": [child],
        "distribution": probability,
        "bound": bound
    } 


# --- Patterns Definitions ---

patterns = []

# 1. Single Task
# Expression: R1
patterns.append({
    "name": "Single Task",
    "expr": "R1",
    "json": task() # Root task
})

# 2. Sequence Two
# Expression: R1, R2
patterns.append({
    "name": "Sequence Two",
    "expr": "R1, R2",
    "json": sequential([task(), task()])
})

# 3. Choice
# Expression: R1 /[C1] R2
patterns.append({
    "name": "Choice",
    "expr": "R1 /[C1] R2",
    "json": choice([task(), task()])
})

# 4. Parallel
# Expression: R1 || R2
patterns.append({
    "name": "Parallel",
    "expr": "R1 || R2",
    "json": parallel([task(), task()])
})

# 5. Loop
# Expression: <R1 [L1]>
patterns.append({
    "name": "Loop",
    "expr": "<R1 [L1]>",
    "json": loop(task(), probability=0.7)
})

# 6. Nature
# Expression: ^[N1] (R1, R2)
patterns.append({
    "name": "Nature",
    "expr": "^[N1] (R1, R2)",
    "json": nature([task(), task()], distribution=[0.3, 0.7])
})

# 7. Sequential + Parallel
# Expression: R1, (R2 || R3), R4
patterns.append({
    "name": "Sequential + Parallel",
    "expr": "R1, (R2 || R3), R4",
    "json": sequential([
        task(),
        sequential([
            parallel([task(), task()]),
            task()
        ])
    ])
})

# 8. Sequential + Choice
# Expression: R1, (R2 /[C1] R3), R4
patterns.append({
    "name": "Sequential + Choice",
    "expr": "R1, (R2 /[C1] R3), R4",
    "json": sequential([
        task(),
        sequential([
            choice([task(), task()]),
            task()
        ])
    ])
})

# 9. Sequential + Loop
# Expression: R1, <R2 [L1]>, R3
patterns.append({
    "name": "Sequential + Loop",
    "expr": "R1, <R2 [L1]>, R3",
    "json": sequential([
        task(),
        sequential([
            loop(task()),
            task()
        ])
    ])
})

# 10. Sequential + Nature
# Expression: R1, ^[N1] (R2, R3), R4
patterns.append({
    "name": "Sequential + Nature",
    "expr": "R1, ^[N1] (R2, R3), R4",
    "json": sequential([
        task(),
        sequential([
            nature([task(), task()], distribution=[0.4, 0.6]),
            task()
        ])
    ])
})

# 11. Complex Parallel
# Expression: R1, ((R2 /[C1] R3) || <R4 [L1]>), R5
patterns.append({
    "name": "Complex Parallel",
    "expr": "R1, ((R2 /[C1] R3) || <R4 [L1]>), R5",
    "json": sequential([
        task(),
        sequential([
            parallel([
                choice([task(), task()]),
                loop(task())
            ]),
            task()
        ])
    ])
})

# 12. Parallel Choice Simple
# Expression: ((R2 /[C1] R3) || R4)
patterns.append({
    "name": "Parallel Choice Simple",
    "expr": "((R2 /[C1] R3) || R4)",
    "json": parallel([
        choice([task(), task()]),
        task()
    ])
})

# 13. Choice of Parallels
# Expression: (R1 || R2) /[C1] (R3 || R4)
patterns.append({
    "name": "Choice of Parallels",
    "expr": "(R1 || R2) /[C1] (R3 || R4)",
    "json": choice([
        parallel([task(), task()]),
        parallel([task(), task()])
    ])
})

# 14. Parallel with Loop
# Expression: R1 || <R2 [L1]>
patterns.append({
    "name": "Parallel with Loop",
    "expr": "R1 || <R2 [L1]>",
    "json": parallel([
        task(),
        loop(task())
    ])
})

# 15. Sequential in Parallel
# Expression: (R1, R2) || (R3, R4)
patterns.append({
    "name": "Sequential in Parallel",
    "expr": "(R1, R2) || (R3, R4)",
    "json": parallel([
        sequential([task(), task()]),
        sequential([task(), task()])
    ])
})

# 16. Nested Choice
# Expression: (R1 /[C1] R2) /[C2] R3
patterns.append({
    "name": "Nested Choice",
    "expr": "(R1 /[C1] R2) /[C2] R3",
    "json": choice([
        choice([task(), task()]),
        task()
    ])
})


def create_notebook(pattern_list):
    cells = []
    
    # 1. Imports
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import sys\n",
            "import os\n",
            "import importlib\n",
            "from IPython.display import SVG, display\n",
            "\n",
            "# Ensure src path is available\n",
            "sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'src')))\n",
            "\n",
            "from model.region import RegionModel\n",
            "from converter.spin import from_region\n",
            "import svg_viz\n",
            "importlib.reload(svg_viz)  # Force reload to get latest changes\n",
            "from svg_viz import spin_to_svg\n",
            "\n",
            "# Also reload converter\n",
            "from converter import spin\n",
            "importlib.reload(spin)\n",
            "\n",
            "print(\"Imports successful! (modules reloaded)\")\n"
        ]
    })
    
    # 2. Iterate patterns
    for p in pattern_list:
        markdown_text = f"## {p['name']}\n**Expression**: `{p['expr']}`"
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [markdown_text]
        })
        
        # We define the JSON dictionary in the cell code
        json_str = json.dumps(p['json'], indent=4)
        
        code_source = f"""# Expression: {p['expr']}
region_json = {json_str}

# 1. Parse JSON to RegionModel (Pydantic handles Enum conversion)
region_model = RegionModel.model_validate(region_json)

# 2. Convert to Petri Net
net, im, fm = from_region(region_model)

# 3. Generate SVG
svg_out = spin_to_svg(net, width=1000, height=500, region=region_model)
display(SVG(svg_out))
"""
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": code_source.splitlines(keepends=True)
        })

    # Notebook structure
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
    print(f"Generating notebook with {len(patterns)} patterns...")
    nb_data = create_notebook(patterns)
    
    with open(OUTPUT_NB, 'w', encoding='utf-8') as f:
        json.dump(nb_data, f, indent=2)
        
    print(f"Notebook saved to {OUTPUT_NB}")
