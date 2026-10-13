# FarmDB — Crop Planning & Farm Input Management

A Python + Flask + SQLite web application for a DBMS project. It provides a dashboard and CRUD workflows for crop plans, fields, farm inputs, soil tests, and summary reports.

## Features
- Responsive farming-themed dashboard
- SQLite database initialized automatically with sample farms, fields, crops, seasons, inputs, and buyers
- Crop planning with season-date validation and status tracking
- Manage fields and farm input inventory
- Record soil tests (pH, nitrogen, phosphorus, potassium)
- Reports for harvest yield, crop-plan status, and input stock
- Basic server-side validation, parameterized SQL, and foreign-key constraints
- Health endpoint at `/health`

> This is a student project starter, not a production farm-management system. It currently seeds one farm and a few sample records. Sales entry, irrigation and labour forms, authentication, and deployment hardening can be added as future improvements.

## Requirements
- Python 3.10+
- VS Code or another editor
- Internet connection for the first install of Flask

## Run locally (VS Code / terminal)
1. Extract the ZIP.
2. Open the extracted `farmdb_project` folder in VS Code.
3. Create a virtual environment:

   **Windows**
   ```bash
   py -m venv .venv
   .venv\\Scripts\\activate
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the website:
   ```bash
   python app.py
   ```
6. Open http://127.0.0.1:5000 in your browser.

The SQLite database file is created automatically on first run. Stop the server with `Ctrl+C`.

## GitHub
1. Create a new repository on GitHub.
2. Upload the extracted project files, or run:
   ```bash
   git init
   git add .
   git commit -m "Initial FarmDB web application"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```
3. Do not commit `.venv/`, secrets, or the generated SQLite database. The `.gitignore` excludes them.

## Project structure
```text
farmdb_project/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── plans.html
│   ├── fields.html
│   ├── inputs.html
│   ├── soil.html
│   └── reports.html
└── static/
    └── style.css
```

## Database entities
`farms`, `fields`, `crops`, `seasons`, `plans`, `inputs`, `applications`, `harvests`, `buyers`, `sales`, `soil_tests`, `irrigation`, and `labour`.

## Notes
- The included SQLite database is local to your computer and is not shared between visitors.
- Debug mode is enabled for local development only. Turn it off before public deployment.
