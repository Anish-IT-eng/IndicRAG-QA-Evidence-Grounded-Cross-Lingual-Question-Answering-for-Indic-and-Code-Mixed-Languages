with open('backend/app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class ResponseStatus')
print(text[idx:idx+500])
