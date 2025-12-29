import json

nb_path = r"C:\Users\danie\Projects\GitHub\Simulator-CPI\json_patterns_test.ipynb"

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

found = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "R1, (R2 || R3), R4" in source:
             # Look for the JSON data in the source
             print("Found Layout Code for Seq+Par:")
             print(source[:500]) # First 500 chars should show the structure if it's there
             found = True
             # We expect nested sequential: 
             # "children": [ ... "type": "sequential" ... ]
             if 'sequential' in source and source.count('sequential') >= 2:
                 print("\n✅ Verified: Nested 'sequential' types found in source code.")
             else:
                 print("\n❌ Failed: Did not find expected nested sequential structure.")
             
             break

if not found:
    print("❌ Could not find Pattern 7 in notebook.")
