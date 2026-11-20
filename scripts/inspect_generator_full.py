with open('backend/app/generation/generator.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def generate_answer')
print(text[idx:])

