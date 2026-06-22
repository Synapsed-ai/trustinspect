import subprocess
from pathlib import Path
import sys

scripts = [
    'scripts/patch_report_header_image.py',
    'scripts/patch_target_registry_extended.py',
    'scripts/patch_analyzer_negative_context.py',
    'scripts/patch_challenge_scanner_runtime.py',
]
for script in scripts:
    print(f'\n==> Running {script}')
    subprocess.check_call([sys.executable, script])
print('\n[+] TrustInspect next-plan patch applied.')
