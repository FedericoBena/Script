## Prima volta: setup (una volta sola)

```
python settings/setup.py
```

---

## Installare librerie

```
python settings/usethis.py numpy pandas matplotlib
```

## Struttura

```
py-scripts-repo/
├── notebooks/        ← scrivi e sperimenta qui
├── models/           ← sposta qui gli script quando sono pronti
├── settings/         ← gestione repo (copia questa cartella per nuovi progetti)
│   ├── setup.py      ← esegui una volta sola per creare il venv
│   └── usethis.py    ← usa questo per installare librerie
├── requirements.txt  ← aggiornato automaticamente
└── .vscode/          ← configurazione VS Code (non toccare)
```
