"""
Flask web front-end for GroupTabTracker (from tracker.py / your code.py).
Keeps one tracker in memory per server process — fine for a demo/portfolio app.
"""
from flask import Flask, render_template, request, redirect, url_for, flash

from tracker import GroupTabTracker, SplitType

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # any string works for demo purposes

tracker = GroupTabTracker(group_name="My Friends Group", currency="₹")


@app.route("/")
def index():
    balances = tracker.calculate_balances()
    plan = tracker.simplify_debts()
    stats = tracker.get_summary_stats()
    return render_template(
        "index.html",
        tracker=tracker,
        balances=balances,
        plan=plan,
        stats=stats,
    )


@app.route("/add_member", methods=["POST"])
def add_member():
    name = request.form.get("name", "").strip()
    try:
        if name:
            added = tracker.add_member(name)
            flash(f"Added {name}." if added else f"{name} is already a member.")
    except ValueError as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))


@app.route("/add_expense", methods=["POST"])
def add_expense():
    try:
        title = request.form.get("title", "").strip()
        amount = float(request.form.get("amount", 0))
        paid_by = request.form.get("paid_by", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        participants = request.form.getlist("participants") or None

        tracker.add_expense(
            title=title,
            amount=amount,
            paid_by=paid_by,
            participants=participants,
            split_type=SplitType.EQUAL,
            category=category,
        )
        flash(f"Added expense '{title}' for {tracker.currency}{amount:.2f}.")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))


@app.route("/settle", methods=["POST"])
def settle():
    try:
        from_u = request.form.get("from_user", "").strip()
        to_u = request.form.get("to_user", "").strip()
        amount = float(request.form.get("amount", 0))
        tracker.record_settlement(from_u, to_u, amount)
        flash(f"Recorded: {from_u} paid {to_u} {tracker.currency}{amount:.2f}.")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
