with open('backend/app/generation/generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'claim' in line.lower() or 'ground' in line.lower() or 'citation' in line.lower() or 'controller' in line.lower():
        print(f"{i+1:3d}: {line.rstrip()}")

