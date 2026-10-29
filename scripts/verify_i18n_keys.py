import re
import json

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

keys = set(re.findall(r'data-i18n="([^"]+)"', html))
keys.update(re.findall(r'data-i18n-tooltip="([^"]+)"', html))
keys.update(re.findall(r'data-i18n-title="([^"]+)"', html))
keys.update(re.findall(r'data-i18n-placeholder="([^"]+)"', html))

with open('ui/i18n.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Extract I18N_TRANSLATIONS JSON
m = re.search(r'const I18N_TRANSLATIONS = (\{[\s\S]*?\n\});', js)
if not m:
    print("ERROR: I18N_TRANSLATIONS not found in ui/i18n.js")
    exit(1)

translations = json.loads(m.group(1))

missing = {}
for lang, dicts in translations.items():
    missing[lang] = []
    for k in sorted(keys):
        parts = k.split('.')
        cur = dicts
        found = True
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                found = False
                break
        if not found:
            missing[lang].append(k)

has_error = False
for lang, miss in missing.items():
    if miss:
        print(f"[{lang}] Missing {len(miss)} keys: {miss}")
        has_error = True
    else:
        print(f"[{lang}] OK! All {len(keys)} keys present.")

if not has_error:
    print("SUCCESS: 100% of all HTML i18n keys are present in all 7 languages!")

