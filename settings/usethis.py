"""
Usa questo per installare librerie nel venv.
Aggiorna requirements.txt in automatico.

    python settings/usethis.py numpy pandas matplotlib
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ  = os.path.join(ROOT, "requirements.txt")

args = sys.argv[1:]
if args and args[0] == "install":
    print("💡 Hai scritto 'install' — lo ignoro e procedo!")
    args = args[1:]

if not args:
    print("❌ Specifica almeno un pacchetto.")
    print("   Uso: python settings/usethis.py numpy pandas")
    sys.exit(1)

print(f"Installo nel venv: {' '.join(args)}")
subprocess.run([sys.executable, "-m", "pip", "install"] + args, check=True)

result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
with open(REQ, "w") as f:
    f.write(result.stdout)

print()
print("Fatto! requirements.txt aggiornato automaticamente.")
