# Software Catalog (Demo)

A public demo of a K12 software catalog: a searchable directory of the apps a district uses, tagged by data privacy agreement (DPA) status, cost, rostering method, access requirements, and subject. It ships with fictional, anonymized sample data and runs without login. The full version lives at [BardSec/software-catalog-public](https://github.com/BardSec/software-catalog-public).

## Features

- **Catalog page:** card grid of software with live text search (name and tagline) and multi-select category filters. Featured entries sort first.
- **Grouped filters:** categories are auto-classified from their names into DPA Status, Cost / School, Rostering, Access, Status, and Subject & Function groups.
- **Detail page** for each entry: description, link, logo, and tags.
- **Admin pages** (`/admin`): add, edit, and delete entries and their categories.
- **Backup:** export the whole catalog as JSON, or import a JSON backup. Import replaces all existing data.
- **JSON API:** `GET /api/software?q=<text>&cat=<id>&cat=<id>`
- **Seed data:** about 25 fictional entries in `software_directory.json`, loaded automatically on first start.
- Security headers (CSP, X-Frame-Options, nosniff) and `ProxyFix` for running behind a reverse proxy.

**Demo mode:** there is no authentication. A banner tells visitors that everyone shares one instance, and anyone can edit the data, including through the admin pages. Don't put real data in a public deployment.

## Tech stack

- Python 3.12, Flask 3.1, Flask-SQLAlchemy
- SQLite (stored in a Docker volume)
- Jinja2 templates, plain CSS, vanilla JavaScript
- Gunicorn, Docker, Docker Compose

## Running

### Docker (recommended)

```bash
cp .env.example .env    # optional
docker compose up -d --build
```

Then open `http://localhost:5000` (or whatever `PORT` you set). The entrypoint seeds the database on first start if it doesn't exist yet.

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///$(pwd)/instance/catalog.db
mkdir -p instance
python seed.py
python wsgi.py
```

To reset the data to the sample set, rerun `python seed.py`. It clears existing entries first.

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session key. Optional; a random key is generated at startup if unset. |
| `PORT` | Host port mapped by Docker Compose (defaults to 5000). |
| `DATABASE_URL` | SQLAlchemy database URI. Set in `docker-compose.yml`; defaults to the SQLite file in `/app/instance`. |
| `FLASK_DEBUG` | Set to `1` to run the dev server in debug mode (`python wsgi.py` only). |

## Project structure

```
app/
  __init__.py          App factory, security headers, logging
  config.py            Config from environment
  models.py            Software, Category (many-to-many), category auto-classification
  catalog/routes.py    Catalog page, detail page, JSON API
  admin/routes.py      Add/edit/delete, JSON export/import
  templates/           Jinja2 templates (catalog, admin, base)
  static/              CSS, catalog.js (search and filter UI), optional logo
seed.py                Loads software_directory.json into the database
software_directory.json  Fictional sample data
entrypoint.sh          Seeds on first run, then starts Gunicorn
```

To show your own logo, drop `logo.png` (or `.svg`, `.jpg`, `.webp`) into `app/static/img/`.
