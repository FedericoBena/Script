"""
Esegui questo script UNA VOLTA SOLA per creare l'ambiente virtuale.
Dalla root del progetto:
    python settings/setup.py
"""
import subprocess
import sys
import os

# Root del progetto = cartella padre di settings/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(ROOT, ".venv")
REQ  = os.path.join(ROOT, "requirements.txt")

print("🔧 Creo l'ambiente virtuale .venv ...")
subprocess.run([sys.executable, "-m", "venv", VENV], check=True)

python = os.path.join(VENV, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV, "bin", "python")

print("📦 Installo le dipendenze da requirements.txt ...")
subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
subprocess.run([python, "-m", "pip", "install", "-r", REQ], check=True)

print()
print("✅ Fatto! Ora:")
print("   2. Ogni nuovo terminale partirà già col venv attivo")
print("   3. Per installare librerie: python settings/usethis.py numpy pandas")
