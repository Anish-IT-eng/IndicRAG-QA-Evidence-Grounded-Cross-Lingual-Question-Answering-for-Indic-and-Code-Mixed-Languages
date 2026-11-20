with open('backend/app/api/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'generate_answer' in l:
        print(f"{i+1}: {l.rstrip()}")
        for j in range(max(0, i-5), min(len(lines), i+10)):
            print(f"  {j+1}: {lines[j].rstrip()}")

