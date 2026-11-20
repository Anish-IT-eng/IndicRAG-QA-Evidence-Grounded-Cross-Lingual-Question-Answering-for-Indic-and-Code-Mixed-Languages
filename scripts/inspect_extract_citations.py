with open('backend/app/generation/generator.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def _extract_citations_from_text')
print(text[idx:idx+2500])

