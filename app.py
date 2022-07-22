import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///recipes.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def apology(message):
    """Render message as an apology to user."""
    return render_template("apology.html", error=message)

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        name = request.form.get("recipe_name")

        rows = db.execute("SELECT * FROM recipes WHERE user_id = ? AND name = ?", session["user_id"], name)
        if len(rows) != 0:
            return apology("That recipe name already exists")

        db.execute("INSERT INTO recipes (user_id, name) VALUES(?, ?)", session["user_id"], name)
        return redirect("/")

    else:
        recipe_list = db.execute("SELECT * FROM recipes WHERE user_id = ?", session["user_id"])
        return render_template("index.html", recipe_list=recipe_list)


@app.route("/delete_recipe", methods=["POST"])
@login_required
def delete_recipe():
    recipe = request.form.get("value")
    db.execute("DELETE FROM recipes WHERE user_id = ? AND name = ?", session["user_id"], recipe)
    return redirect("/")


@app.route("/list", methods=["GET", "POST"])
@login_required
def shopping_list():
    if request.method == "POST":
        item = request.form.get("item")
        notes = request.form.get("notes")

        rows = db.execute("SELECT * FROM list WHERE user_id = ? AND item = ?", session["user_id"], item)
        if len(rows) != 0:
            return apology("Item already in list")

        db.execute("INSERT INTO list (user_id, item, note, status) VALUES(?, ?, ?, 'on')", session["user_id"], item, notes)
        return redirect("/list")

    else:
        all_items = db.execute("SELECT * FROM list WHERE user_id = ?", session["user_id"])
        return render_template("list.html", all_items=all_items)


@app.route("/toggle_item", methods=["POST"])
@login_required
def toggle_item():
    status = request.form.get("status")
    item = request.form.get("item")

    if status == "on":
        db.execute("UPDATE list SET status='off' WHERE user_id = ? AND item = ?", session["user_id"], item)

    else:
        db.execute("UPDATE list SET status='on' WHERE user_id = ? AND item = ?", session["user_id"], item)
    return redirect("/list")

@app.route("/delete_item", methods=["POST"])
@login_required
def delete_item():
    item = request.form.get("value")
    db.execute("DELETE FROM list WHERE user_id = ? AND item = ?", session["user_id"], item)
    return redirect("/list")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        verify_password = request.form.get("confirmation")

        # verifies all fields are filled
        if username == "" or password == "" or verify_password == "":
            return apology("All fields must be completed")
        # verifies password matched the verify password field
        if password != verify_password:
            return apology("Password fields do not match")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        # verifies that the username is not already in use
        if len(rows) != 0:
            return apology("Username is unavailable")

        hash = generate_password_hash(password)
        # inserts the username and hash for the password into the users table
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        # sets the session to be for the current user
        session["user_id"] = user[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/recipe", methods=["GET", "POST"])
@login_required
def recipe():
    if request.method == "POST":
        # get the recipe name
        recipe_name = request.form.get("recipeName")
        db.execute("UPDATE users SET current_recipe = ? WHERE id = ?", recipe_name, session["user_id"])
        recipe = db.execute("SELECT * FROM recipes WHERE name = ? AND user_id = ?", recipe_name, session["user_id"])
        # send the recipe name variable to the recipe page when it loads
        ingredient_list = db.execute("SELECT * FROM ingredients WHERE user_id = ? AND recipe_id = ?", session["user_id"], recipe[0]["id"])
        return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list)
    else: 
        current_recipe = db.execute("SELECT current_recipe FROM users WHERE id = ?", session["user_id"])
        recipe = db.execute("SELECT * FROM recipes WHERE name = ? AND user_id = ?", current_recipe[0]["current_recipe"], session["user_id"])
        ingredient_list = db.execute("SELECT * FROM ingredients WHERE user_id = ? AND recipe_id = ?", session["user_id"], recipe[0]["id"])
        return render_template("recipe.html", recipe=recipe, ingredient_list=ingredient_list)


@app.route("/ingredient", methods=["POST"])
@login_required
def ingredient():
    ingredient = request.form.get("ingredient")
    amount = request.form.get("ingredient_amount")
    recipe_id = request.form.get("ingredient_recipe")

    rows = db.execute("SELECT * FROM ingredients WHERE user_id = ? AND recipe_id = ? AND item = ?", session["user_id"], recipe_id, ingredient)
    if len(rows) != 0:
        return apology("Ingredient already in recipe")

    db.execute("INSERT INTO ingredients (user_id, recipe_id, amount, item) VALUES(?, ?, ?, ?)", session["user_id"], recipe_id, amount, ingredient)
    return redirect("/recipe")


@app.route("/delete_ingredient", methods=["POST"])
@login_required
def delete_ingredient():
    recipe_id = request.form.get("recipe_id")
    recipe_name = request.form.get("recipe_name")
    db.execute("DELETE FROM ingredients WHERE user_id = ? AND recipe_id = ? AND item = ?", session["user_id"], recipe_id, recipe_name)
    return redirect("/recipe")


@app.route("/prep", methods=["POST"])
@login_required
def prep():
    prep = request.form.get("prep")
    name = request.form.get("prep_recipe")
    db.execute("UPDATE recipes SET prep_direction = ? WHERE user_id = ? AND name = ?", prep, session["user_id"], name)
    return redirect("/recipe")


@app.route("/cook", methods=["POST"])
@login_required
def cook():
    cook = request.form.get("cook")
    name = request.form.get("cook_recipe")
    db.execute("UPDATE recipes SET cook_direction = ? WHERE user_id = ? AND name = ?", cook, session["user_id"], name)
    return redirect("/recipe")


@app.route("/note", methods=["POST"])
@login_required
def note():
    notes = request.form.get("note")
    name = request.form.get("note_recipe")
    db.execute("UPDATE recipes SET notes = ? WHERE user_id = ? AND name = ?", notes, session["user_id"], name)
    return redirect("/recipe")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user_id = session["user_id"]
    if request.method == "POST":
        # get old password hash
        password_hash = db.execute("SELECT hash FROM users WHERE id = ?", user_id)

        # get all form values
        old = request.form.get("old_password")
        new = request.form.get("password")
        verify = request.form.get("confirmation")
        # ensure no form fields are empty
        if old == "" or new == "" or verify == "":
            return apology("Complete all fields")
        # verify that new password fields match
        if new != verify:
            return apology("New passwords don't match")
        # verify that the old password is correct
        if not check_password_hash(password_hash[0]["hash"], old):
            return apology("Incorrect password")
        # create a hash for the new password
        new_hash = generate_password_hash(new)
        # update SQL table with new hash
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, user_id)
        return apology("Success")

    else:
        # get username
        username = db.execute("SELECT username FROM users WHERE id = ?", user_id)
        return render_template("account.html", username=username[0]["username"])

