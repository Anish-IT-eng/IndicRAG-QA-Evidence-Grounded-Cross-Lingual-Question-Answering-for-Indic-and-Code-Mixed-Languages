with open('backend/tests/test_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'generate_answer' in l:
        print(f"{i+1}: {l.rstrip()}")

