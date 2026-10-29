import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

print('data-i18n count:', len(re.findall(r'data-i18n="([^"]+)"', text)))
print('data-i18n-tooltip count:', len(re.findall(r'data-i18n-tooltip="([^"]+)"', text)))
print('data-i18n-title count:', len(re.findall(r'data-i18n-title="([^"]+)"', text)))
print('data-i18n-placeholder count:', len(re.findall(r'data-i18n-placeholder="([^"]+)"', text)))

