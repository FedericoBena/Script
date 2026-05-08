[ -f ~/.bashrc ] && source ~/.bashrc

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$REPO_ROOT/.venv"

if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
else
    echo "⚠️  Venv non trovato. Esegui: python settings/setup.py"
fi

pip() {
    if [ "$1" = "install" ]; then
        shift
        echo ""
        echo "🚫 'pip install' diretto non aggiorna requirements.txt!"
        echo "✅ Usa invece:"
        echo "   python settings/usethis.py $@"
        echo ""
    else
        command pip "$@"
    fi
}
export -f pip
