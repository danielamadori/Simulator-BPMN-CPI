import re

filepath = 'src/generate_json_test_nb.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace task("R1"), task("R2"), etc. with task()
content = re.sub(r'task\("R\d+"\)', 'task()', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! Replaced all task(\"R...\") with task()")
