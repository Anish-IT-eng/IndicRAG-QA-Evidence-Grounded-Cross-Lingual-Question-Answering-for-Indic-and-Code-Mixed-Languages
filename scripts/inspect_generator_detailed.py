with open('backend/app/generation/generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("".join(lines[120:175]))
print("="*60)
print("".join(lines[275:315]))

