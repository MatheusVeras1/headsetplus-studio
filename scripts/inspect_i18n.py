import re
import json

with open('ui/i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Match the JS object
m = re.search(r'const I18N_TRANSLATIONS = (\{[\s\S]*?\n\};)', content)
if m:
    js_obj = m.group(1).rstrip(';')
    # We can parse the keys with regex or simple AST
    languages = re.findall(r'"([a-z]{2}-[A-Z]{2})":\s*\{', js_obj)
    print("Found languages:", languages)
    
    # Check pt-BR sections
    pt_section = re.search(r'"pt-BR":\s*\{(.*?)\n  \},', js_obj, re.DOTALL)
    if pt_section:
        subsections = re.findall(r'(\w+):\s*\{', pt_section.group(1))
        print("pt-BR subsections:", subsections)
        for sub in subsections:
            sub_body = re.search(r'' + sub + r':\s*\{(.*?)\}', pt_section.group(1), re.DOTALL)
            if sub_body:
                keys = re.findall(r'(\w+):', sub_body.group(1))
                print(f"  {sub}: {keys}")

