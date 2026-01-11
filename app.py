from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret")
DATABASE = "wevote.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ordering INTEGER NOT NULL DEFAULT 0
        );
    """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS nominees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            votes INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
    """
    )
    db.commit()


def seed_sample_ballot():
    db = get_db()
    c = db.execute("SELECT COUNT(*) as cnt FROM categories").fetchone()["cnt"]
    if c == 0:
        categories = [
            ("President", ["Alice", "Bob", "Charlie"]),
            ("Secretary", ["Dana", "Eli"]),
            ("Treasurer", ["Fay", "George"]),
        ]
        for idx, (cat, noms) in enumerate(categories):
            cur = db.execute("INSERT INTO categories (name, ordering) VALUES (?, ?)", (cat, idx))
            cat_id = cur.lastrowid
            db.executemany(
                "INSERT INTO nominees (category_id, name, votes) VALUES (?, ?, 0)",
                [(cat_id, n) for n in noms],
            )
        db.commit()


@app.before_first_request
def startup():
    init_db()
    seed_sample_ballot()


def get_categories():
    db = get_db()
    return db.execute("SELECT id, name FROM categories ORDER BY ordering, id").fetchall()


def get_nominees(category_id):
    db = get_db()
    return db.execute("SELECT id, name, votes FROM nominees WHERE category_id = ? ORDER BY id", (category_id,)).fetchall()


@app.route("/")
def index():
    if session.get("voted"):
        return render_template("index.html", voted=True)
    categories = get_categories()
    return render_template("index.html", voted=False, categories=categories)


@app.route("/start", methods=("POST",))
def start():
    if session.get("voted"):
        flash("You already voted in this session.", "info")
        return redirect(url_for("index"))
    categories = get_categories()
    if not categories:
        flash("No categories available.", "warning")
        return redirect(url_for("index"))
    session["selections"] = {}
    session["category_order"] = [str(c["id"]) for c in categories]
    session["current_index"] = 0
    return redirect(url_for("vote", index=0))


@app.route("/vote/<int:index>", methods=("GET", "POST"))
def vote(index):
    if session.get("voted"):
        flash("You already voted in this session.", "info")
        return redirect(url_for("index"))
    order = session.get("category_order")
    if order is None:
        flash("Please start the ballot first.", "warning")
        return redirect(url_for("index"))
    if index < 0 or index >= len(order):
        flash("Invalid category index.", "danger")
        return redirect(url_for("index"))
    cat_id = int(order[index])
    db = get_db()
    category = db.execute("SELECT id, name FROM categories WHERE id = ?", (cat_id,)).fetchone()
    nominees = get_nominees(cat_id)
    if request.method == "POST":
        selected = request.form.get("nominee")
        if not selected:
            flash("Please select a nominee.", "danger")
            return redirect(url_for("vote", index=index))
        selections = session.get("selections", {})
        selections[str(cat_id)] = selected
        session["selections"] = selections
        return redirect(url_for("confirm", index=index))
    return render_template("vote.html", category=category, nominees=nominees, index=index, total=len(order))


@app.route("/confirm/<int:index>", methods=("GET", "POST"))
def confirm(index):
    if session.get("voted"):
        flash("You already voted in this session.", "info")
        return redirect(url_for("index"))
    order = session.get("category_order")
    if order is None:
        flash("Please start the ballot first.", "warning")
        return redirect(url_for("index"))
    if index < 0 or index >= len(order):
        flash("Invalid category index.", "danger")
        return redirect(url_for("index"))
    cat_id = int(order[index])
    db = get_db()
    category = db.execute("SELECT id, name FROM categories WHERE id = ?", (cat_id,)).fetchone()
    nominee_id = session.get("selections", {}).get(str(cat_id))
    if nominee_id is None:
        flash("No selection found to confirm.", "warning")
        return redirect(url_for("vote", index=index))
    nominee = db.execute("SELECT id, name FROM nominees WHERE id = ? AND category_id = ?", (int(nominee_id), cat_id)).fetchone()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "confirm":
            db.execute("UPDATE nominees SET votes = votes + 1 WHERE id = ? AND category_id = ?", (nominee["id"], cat_id))
            db.commit()
            next_index = index + 1
            if next_index >= len(order):
                session["voted"] = True
                flash("All votes recorded. Thank you!", "success")
                return redirect(url_for("complete"))
            else:
                flash(f"Vote for '{category['name']}' recorded.", "success")
                return redirect(url_for("vote", index=next_index))
        else:
            return redirect(url_for("vote", index=index))
    return render_template("confirm.html", category=category, nominee=nominee, index=index, total=len(order))


@app.route("/complete")
def complete():
    voted = session.get("voted", False)
    selections = session.get("selections", {})
    db = get_db()
    picks = []
    for cat_id_str, nominee_id_str in selections.items():
        try:
            cat_id = int(cat_id_str)
            nominee_id = int(nominee_id_str)
        except ValueError:
            continue
        cat = db.execute("SELECT name FROM categories WHERE id = ?", (cat_id,)).fetchone()
        nom = db.execute("SELECT name FROM nominees WHERE id = ?", (nominee_id,)).fetchone()
        if cat and nom:
            picks.append({"category": cat["name"], "nominee": nom["name"]})
    return render_template("complete.html", voted=voted, picks=picks)


@app.route("/results")
def results():
    db = get_db()
    categories = db.execute("SELECT id, name FROM categories ORDER BY ordering, id").fetchall()
    data = []
    for cat in categories:
        noms = db.execute("SELECT name, votes FROM nominees WHERE category_id = ? ORDER BY id", (cat["id"],)).fetchall()
        total = sum([n["votes"] for n in noms])
        items = []
        for n in noms:
            pct = (n["votes"] / total * 100) if total > 0 else 0
            items.append({"name": n["name"], "votes": n["votes"], "pct": round(pct, 1)})
        data.append({"category": cat["name"], "total": total, "nominees": items})
    return render_template("results.html", data=data)


@app.route("/admin/reset", methods=("POST",))
def admin_reset():
    db = get_db()
    db.execute("DELETE FROM nominees;")
    db.execute("DELETE FROM categories;")
    db.commit()
    seed_sample_ballot()
    flash("Database reset and sample ballot seeded.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
