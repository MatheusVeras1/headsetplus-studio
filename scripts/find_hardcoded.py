import re

def check_file(fname):
    print(f"=== {fname} ===")
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    # Check for textContent or innerHTML assignments with Portuguese words
    matches = re.findall(r'(\w+\.(?:textContent|innerText)\s*=\s*[^;\n]+)', content)
    for m in matches:
        if any(w in m for w in ['Conect', 'Modo', 'Silên', 'Deslig', 'Perfil', 'Reset', 'Carreg', 'Fone']):
            print("  ", m[:100])

check_file('ui/app.js')
check_file('ui/eq_engine.js')
check_file('ui/acoustic_lab.js')

