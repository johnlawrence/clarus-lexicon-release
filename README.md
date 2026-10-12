# Multilingual Lexicon of Digital Forensics

A web app for browsing the multilingual digital forensics lexicon developed in the CLARUS project. Search or browse terms and open a full entry for each one: definition, usage example, collocates and links to the term's equivalents in the other languages.

Languages: English, Finnish, Greek, Czech, Portuguese.

## Running

With Docker:

```bash
docker compose up --build
```

Or locally:

```bash
pip install -r requirements.txt
python run.py
```

## Layout

- `app/` – the Flask app: routes, templates, static files and translation catalogs
- `data/lexicon.db` – the SQLite database the app reads
- `run.py` – entry point

## Credits

Lexicon by Dr Duygu Candarli and Dr James Balfour; interface by Dr John Lawrence. Funded by Horizon Europe and UKRI. See the About page in the app for the full team and funding details.
