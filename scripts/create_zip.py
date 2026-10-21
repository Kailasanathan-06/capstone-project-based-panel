import os
import zipfile

src_dir = r'C:\Users\mkail\capstone project\project vs code\SecureDT'
release_dir = r'C:\Users\mkail\capstone project\project vs code\release'
os.makedirs(release_dir, exist_ok=True)
zip_path = os.path.join(release_dir, 'Intelligent_Secure_Task_Scheduling_Django_MySQL_FINAL.zip')

EXCLUDE_DIR_NAMES = {'__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'logs', 'tmp', 'cache', 'media', '.'}
EXCLUDE_FILE_NAMES = {'.env', 'db.sqlite3', '.DS_Store'}

files_to_zip = []
for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
    for f in files:
        if f in EXCLUDE_FILE_NAMES or f.endswith('.pyc') or f.endswith('.log'):
            continue
        filepath = os.path.join(root, f)
        relpath = os.path.relpath(filepath, os.path.dirname(src_dir))
        files_to_zip.append((filepath, relpath))

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for filepath, relpath in files_to_zip:
        zf.write(filepath, relpath)

print('ZIP created:', zip_path)
print('ZIP size:', os.path.getsize(zip_path), 'bytes')
print('Files included:', len(files_to_zip))

excl = []
with zipfile.ZipFile(zip_path, 'r') as zf:
    names = zf.namelist()
    print('Total entries:', len(names))
    for n in names:
        b = os.path.basename(n)
        if b == '.env' or '__pycache__' in n or 'node_modules' in n or '.venv' in n:
            excl.append(n)
print('Excluded-check violations:', excl if excl else 'NONE - clean')
print('manage.py present:', any('/manage.py' in n for n in names))
print('requirements.txt present:', any(n.endswith('/requirements.txt') for n in names))
print('.env.example present:', any(n.endswith('/.env.example') for n in names))
print('PDFs present:', sum(1 for n in names if n.endswith('.pdf')))