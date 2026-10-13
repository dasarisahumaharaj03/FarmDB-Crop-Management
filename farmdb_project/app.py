from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "farmdb.sqlite3"
app = Flask(__name__)
app.secret_key = "change-this-secret-key"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS farms (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, location TEXT NOT NULL, owner TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fields (
 id INTEGER PRIMARY KEY AUTOINCREMENT, farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
 name TEXT NOT NULL, area REAL NOT NULL CHECK(area > 0), soil_type TEXT NOT NULL DEFAULT 'Loam'
);
CREATE TABLE IF NOT EXISTS crops (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, duration_days INTEGER NOT NULL CHECK(duration_days > 0)
);
CREATE TABLE IF NOT EXISTS seasons (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, start_date TEXT NOT NULL, end_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
 id INTEGER PRIMARY KEY AUTOINCREMENT, field_id INTEGER NOT NULL REFERENCES fields(id),
 crop_id INTEGER NOT NULL REFERENCES crops(id), season_id INTEGER NOT NULL REFERENCES seasons(id),
 sow_date TEXT NOT NULL, harvest_date TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'Planned' CHECK(status IN ('Planned','Sown','Harvested')),
 CHECK(harvest_date > sow_date)
);
CREATE TABLE IF NOT EXISTS inputs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('Fertilizer','Seed','Pesticide')),
 unit TEXT NOT NULL, unit_cost REAL NOT NULL CHECK(unit_cost > 0),
 stock REAL NOT NULL DEFAULT 0 CHECK(stock >= 0)
);
CREATE TABLE IF NOT EXISTS applications (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES plans(id),
 input_id INTEGER NOT NULL REFERENCES inputs(id), applied_on TEXT NOT NULL, quantity REAL NOT NULL CHECK(quantity > 0)
);
CREATE TABLE IF NOT EXISTS harvests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES plans(id),
 harvested_on TEXT NOT NULL, quantity_kg REAL NOT NULL CHECK(quantity_kg >= 0)
);
CREATE TABLE IF NOT EXISTS buyers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, phone TEXT
);
CREATE TABLE IF NOT EXISTS sales (
 id INTEGER PRIMARY KEY AUTOINCREMENT, harvest_id INTEGER NOT NULL REFERENCES harvests(id),
 buyer_id INTEGER NOT NULL REFERENCES buyers(id), sold_on TEXT NOT NULL,
 quantity_kg REAL NOT NULL CHECK(quantity_kg > 0), price_per_kg REAL NOT NULL CHECK(price_per_kg >= 0)
);
CREATE TABLE IF NOT EXISTS soil_tests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, field_id INTEGER NOT NULL REFERENCES fields(id),
 tested_on TEXT NOT NULL, ph REAL NOT NULL CHECK(ph BETWEEN 0 AND 14),
 nitrogen REAL NOT NULL CHECK(nitrogen >= 0), phosphorus REAL NOT NULL CHECK(phosphorus >= 0),
 potassium REAL NOT NULL CHECK(potassium >= 0)
);
CREATE TABLE IF NOT EXISTS irrigation (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES plans(id),
 watered_on TEXT NOT NULL, method TEXT NOT NULL CHECK(method IN ('Flood','Drip','Sprinkler')),
 water_kl REAL NOT NULL CHECK(water_kl > 0)
);
CREATE TABLE IF NOT EXISTS labour (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES plans(id),
 worker TEXT NOT NULL, activity TEXT NOT NULL, work_date TEXT NOT NULL,
 hours REAL NOT NULL CHECK(hours > 0), wage_per_hour REAL NOT NULL CHECK(wage_per_hour > 0)
);
"""

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con:
        con.executescript(SCHEMA)
        if con.execute("SELECT COUNT(*) FROM farms").fetchone()[0] == 0:
            con.execute("INSERT INTO farms(name,location,owner) VALUES(?,?,?)", ("Green Valley Farm","Telangana, India","Farm Owner"))
            con.execute("INSERT INTO fields(farm_id,name,area,soil_type) VALUES(1,?,?,?)", ("North Plot",5.0,"Black cotton"))
            con.executemany("INSERT INTO crops(name,duration_days) VALUES(?,?)", [("Rice",120),("Cotton",160),("Maize",100),("Wheat",120)])
            con.executemany("INSERT INTO seasons(name,start_date,end_date) VALUES(?,?,?)", [
                ("Kharif 2026","2026-06-01","2026-10-31"),("Rabi 2026-27","2026-11-01","2027-03-31")])
            con.executemany("INSERT INTO inputs(name,kind,unit,unit_cost,stock) VALUES(?,?,?,?,?)", [
                ("Urea","Fertilizer","kg",6.5,500),("Paddy Seed","Seed","kg",55,100),("Neem-based pesticide","Pesticide","L",250,25)])
            con.execute("INSERT INTO buyers(name,phone) VALUES(?,?)", ("Local Market",""))
            con.commit()

@app.context_processor
def common():
    return {"farm_name": "FarmDB"}

@app.route("/")
def dashboard():
    with connect() as con:
        stats = {
            "farms": con.execute("SELECT COUNT(*) FROM farms").fetchone()[0],
            "fields": con.execute("SELECT COUNT(*) FROM fields").fetchone()[0],
            "plans": con.execute("SELECT COUNT(*) FROM plans").fetchone()[0],
            "inputs": con.execute("SELECT COUNT(*) FROM inputs").fetchone()[0],
            "area": con.execute("SELECT COALESCE(SUM(area),0) FROM fields").fetchone()[0],
            "harvest": con.execute("SELECT COALESCE(SUM(quantity_kg),0) FROM harvests").fetchone()[0],
        }
        recent = con.execute("""SELECT p.id, f.name AS field_name, c.name AS crop_name, p.sow_date,
            p.harvest_date, p.status FROM plans p JOIN fields f ON f.id=p.field_id
            JOIN crops c ON c.id=p.crop_id ORDER BY p.id DESC LIMIT 6""").fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)

@app.route("/plans", methods=["GET","POST"])
def plans():
    with connect() as con:
        if request.method == "POST":
            try:
                field_id = int(request.form["field_id"])
                crop_id = int(request.form["crop_id"])
                season_id = int(request.form["season_id"])
                sow, harvest = request.form["sow_date"], request.form["harvest_date"]
                season = con.execute("SELECT * FROM seasons WHERE id=?", (season_id,)).fetchone()
                if not season or not (season["start_date"] <= sow < harvest <= season["end_date"]):
                    raise ValueError("Crop dates must fall within the selected season and harvest must be after sowing.")
                con.execute("INSERT INTO plans(field_id,crop_id,season_id,sow_date,harvest_date,status) VALUES(?,?,?,?,?,?)",
                            (field_id,crop_id,season_id,sow,harvest,request.form["status"]))
                con.commit()
                flash("Crop plan added successfully.", "success")
                return redirect(url_for("plans"))
            except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
                flash(str(exc) or "Please check the entered values.", "error")
        fields = con.execute("SELECT * FROM fields ORDER BY name").fetchall()
        crops = con.execute("SELECT * FROM crops ORDER BY name").fetchall()
        seasons = con.execute("SELECT * FROM seasons ORDER BY start_date").fetchall()
        rows = con.execute("""SELECT p.*, f.name field_name, c.name crop_name, s.name season_name
            FROM plans p JOIN fields f ON f.id=p.field_id JOIN crops c ON c.id=p.crop_id
            JOIN seasons s ON s.id=p.season_id ORDER BY p.id DESC""").fetchall()
    return render_template("plans.html", fields=fields, crops=crops, seasons=seasons, rows=rows)

@app.route("/fields", methods=["GET","POST"])
def fields():
    with connect() as con:
        if request.method == "POST":
            try:
                con.execute("INSERT INTO fields(farm_id,name,area,soil_type) VALUES(1,?,?,?)",
                            (request.form["name"].strip(), float(request.form["area"]), request.form["soil_type"].strip() or "Loam"))
                con.commit()
                flash("Field added.", "success")
                return redirect(url_for("fields"))
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(f"Could not add field: {exc}", "error")
        rows = con.execute("SELECT f.*, farms.name farm_name FROM fields f JOIN farms ON farms.id=f.farm_id ORDER BY f.id DESC").fetchall()
    return render_template("fields.html", rows=rows)

@app.route("/inputs", methods=["GET","POST"])
def inputs():
    with connect() as con:
        if request.method == "POST":
            try:
                con.execute("INSERT INTO inputs(name,kind,unit,unit_cost,stock) VALUES(?,?,?,?,?)",
                            (request.form["name"].strip(), request.form["kind"], request.form["unit"].strip(),
                             float(request.form["unit_cost"]), float(request.form["stock"])))
                con.commit()
                flash("Farm input added.", "success")
                return redirect(url_for("inputs"))
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(f"Could not add input: {exc}", "error")
        rows = con.execute("SELECT * FROM inputs ORDER BY name").fetchall()
    return render_template("inputs.html", rows=rows)

@app.route("/soil", methods=["GET","POST"])
def soil():
    with connect() as con:
        if request.method == "POST":
            try:
                ph = float(request.form["ph"])
                if not 0 <= ph <= 14: raise ValueError("pH must be between 0 and 14.")
                con.execute("""INSERT INTO soil_tests(field_id,tested_on,ph,nitrogen,phosphorus,potassium)
                    VALUES(?,?,?,?,?,?)""", (int(request.form["field_id"]),request.form["tested_on"],ph,
                    float(request.form["nitrogen"]),float(request.form["phosphorus"]),float(request.form["potassium"])))
                con.commit()
                flash("Soil test saved.", "success")
                return redirect(url_for("soil"))
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(f"Could not save soil test: {exc}", "error")
        fields = con.execute("SELECT * FROM fields ORDER BY name").fetchall()
        rows = con.execute("SELECT t.*, f.name field_name FROM soil_tests t JOIN fields f ON f.id=t.field_id ORDER BY t.id DESC").fetchall()
    return render_template("soil.html", fields=fields, rows=rows)

@app.route("/reports")
def reports():
    with connect() as con:
        yield_rows = con.execute("""SELECT c.name crop_name, SUM(h.quantity_kg) total_kg,
            ROUND(SUM(h.quantity_kg)/NULLIF(SUM(f.area),0),1) kg_per_acre
            FROM harvests h JOIN plans p ON p.id=h.plan_id JOIN crops c ON c.id=p.crop_id
            JOIN fields f ON f.id=p.field_id GROUP BY c.id ORDER BY total_kg DESC""").fetchall()
        stock = con.execute("SELECT name,kind,stock,unit,unit_cost FROM inputs ORDER BY name").fetchall()
        plans_count = con.execute("SELECT status,COUNT(*) n FROM plans GROUP BY status").fetchall()
    return render_template("reports.html", yield_rows=yield_rows, stock=stock, plans_count=plans_count)

@app.route("/delete/<table>/<int:row_id>", methods=["POST"])
def delete_record(table, row_id):
    allowed = {"plans":"plans", "fields":"fields", "inputs":"inputs", "soil_tests":"soil_tests"}
    if table not in allowed:
        flash("Delete action not allowed.", "error")
        return redirect(url_for("dashboard"))
    try:
        with connect() as con:
            con.execute(f"DELETE FROM {allowed[table]} WHERE id=?", (row_id,))
            con.commit()
        flash("Record deleted.", "success")
    except sqlite3.IntegrityError as exc:
        flash(f"Cannot delete this record because other records depend on it: {exc}", "error")
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/health")
def health():
    return {"status":"ok","database":"SQLite","project":"FarmDB"}

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
