import os
import cs50

from datetime import timedelta
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Table, Text, delete, update, select, asc
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base
from functools import wraps
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "superSecretKey"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)


# railway postgres url
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:2zcW58qlJgF4vNQ2gGgt@containers-us-west-111.railway.app:7408/railway"

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URL

# dev postgres db
#app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:Eillek86@localhost/postgres_recipes'

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text(), nullable=False)
    hash = db.Column(db.Text(), nullable=False)
    current_recipe = db.Column(db.Text())
    
    def __init__(self, username, hash, current_recipe):
        self.username = username
        self.hash = hash
        self.current_recipe = current_recipe


class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    prep_direction = db.Column(db.Text())
    cook_direction = Column(db.Text())
    notes = db.Column(db.Text())
    name = db.Column(db.Text())

    def __init__(self, user_id, prep_direction, cook_direction, notes, name):
        self.user_id = user_id
        self.prep_direction = prep_direction
        self.cook_direction = cook_direction
        self.notes = notes
        self.name = name


class Ingredients(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    recipe_id = db.Column(db.Integer)
    amount = db.Column(db.Text())
    item = db.Column(db.Text())

    def __init__(self, user_id, recipe_id, amount, item):
        self.user_id = user_id
        self.recipe_id = recipe_id
        self.amount = amount
        self.item = item


class List(db.Model):
    __tablename__ = 'list'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    item = db.Column(db.Text())
    note = db.Column(db.Text())
    status = db.Column(db.Text())

    def __init__(self, user_id, item, note, status):
        self.user_id = user_id
        self.item = item
        self.note = note
        self.status = status

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    """
    Decorate routes to require login. More info in link.
    https://flask.palletsprojects.com/en/2.1.x/patterns/viewdecorators/
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

        rows = db.session.query(Recipe).filter(Recipe.name == name).filter(Recipe.user_id == session["user_id"]).count()
        if rows != 0:
            recipe_list = db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).order_by(asc(Recipe.id))
            return render_template("index.html", recipe_list=recipe_list, error="That recipe name already exists")

        data = Recipe(user_id=session["user_id"], name=name, prep_direction="", cook_direction="", notes="")
        db.session.add(data)
        db.session.commit()

        return redirect("/")

    else:
        recipe_list = db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).order_by(asc(Recipe.id))
        return render_template("index.html", recipe_list=recipe_list)


@app.route("/delete_recipe", methods=["POST"])
@login_required
def delete_recipe():
    recipe = request.form.get("value")
    db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).filter(Recipe.name == recipe).delete()
    db.session.commit()
    return redirect("/")


@app.route("/list", methods=["GET", "POST"])
@login_required
def shopping_list():
    if request.method == "POST":
        item = request.form.get("item")
        notes = request.form.get("notes")

        rows = db.session.query(List).filter(List.user_id == session["user_id"]).filter(List.item == item).count()
        if rows != 0:
            all_items = db.session.query(List).filter(List.user_id == session["user_id"]).order_by(asc(List.id))
            return render_template("list.html", all_items=all_items, error="Item already in list")

        data = List(user_id=session["user_id"], item=item, note=notes, status="on")
        db.session.add(data)
        db.session.commit()
        return redirect("/list")

    else:
        all_items = db.session.query(List).filter(List.user_id == session["user_id"]).order_by(asc(List.id))
        return render_template("list.html", all_items=all_items)


@app.route("/toggle_item", methods=["POST"])
@login_required
def toggle_item():
    status = request.form.get("status")
    item = request.form.get("item")

    if status == "on":
        user_row = db.session.query(List).filter(List.user_id == session["user_id"]).filter(List.item == item).first()
        user_row.status = "off"
        db.session.commit()

    else:
        user_row = db.session.query(List).filter(List.user_id == session["user_id"]).filter(List.item == item).first()
        user_row.status = "on"
        db.session.commit()
    return redirect("/list")


@app.route("/delete_item", methods=["POST"])
@login_required
def delete_item():
    item = request.form.get("value")
    db.session.query(List).filter(List.user_id == session["user_id"]).filter(List.item == item).delete()
    db.session.commit()
    return redirect("/list")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        verify_password = request.form.get("confirmation")

        # verifies all fields are filled
        if username == "" or password == "" or verify_password == "":
            return render_template("register.html", error="Please complete all fields")
        # verifies password matched the verify password field
        if password != verify_password:
            return render_template("register.html", error="Password fields do not match")

        # verifies that the username is not already in use
        rows = db.session.query(User).filter(User.username == username).count()
        if rows != 0:
            return render_template("register.html", error="Username is unavailable")

        hash = generate_password_hash(password)

        # inserts the username and hash for the password into the users table
        data = User(username=username, hash=hash, current_recipe="")
        db.session.add(data)
        db.session.commit()
    
        # sets the session to be for the current user
        session["user_id"] = db.session.query(User).filter(User.username == username).first().id

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
            return render_template("login.html", error="Please enter your username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="Please enter your password")

        # Query database for username
        username = request.form.get("username")
        user_data = db.session.query(User).filter(User.username == username)
        rows = db.session.query(User).filter(User.username == username).count()

        # Ensure username exists and password is correct
        if rows != 1 or not check_password_hash(user_data[0].hash, request.form.get("password")):
            return render_template("login.html", error="Invalid username and/or password")

        # Remember which user has logged in
        session.permanent = True
        session["user_id"] = user_data[0].id

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
        # get the recipe name the user selected
        recipe_name = request.form.get("recipeName")
        # set that recipe as the user's currently selected recipe in the db
        db.session.query(User).filter(User.id == session["user_id"]).first().current_recipe = recipe_name
        db.session.commit()
        # gets the db row for that recipe
        recipe = db.session.query(Recipe).filter(Recipe.name == recipe_name).filter(Recipe.user_id == session["user_id"]).first()
        # query the ingredients table for all ingredients for the current recipe
        ingredient_list = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe.id)
        # renders the template and sends the variables for use in the html/jinja
        prep_steps = recipe.prep_direction.split("\n")
        cook_steps = recipe.cook_direction.split("\n")
        note_steps = recipe.notes.split("\n")
        return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list, prep_steps=prep_steps, cook_steps=cook_steps, note_steps=note_steps)
    else:
        # get the name of the current recipe from the user table in the db
        recipe_name = db.session.query(User).filter(User.id == session["user_id"]).first().current_recipe
        # query the db row for the recipe
        recipe = db.session.query(Recipe).filter(Recipe.name == recipe_name).filter(Recipe.user_id == session["user_id"]).first()
        # query the ingredients table for all ingredients for the current recipe
        ingredient_list = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe.id)
        # renders the template and sends the variables for use in the html/jinja
        prep_steps = recipe.prep_direction.split("\n")
        cook_steps = recipe.cook_direction.split("\n")
        note_steps = recipe.notes.split("\n")
        return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list, prep_steps=prep_steps, cook_steps=cook_steps, note_steps=note_steps)


@app.route("/ingredientToList", methods=["POST"])
@login_required
def ingredientToList():
    ingredient = request.form.get("ingredientItem")
    # query to see if ingredient is already in user's list
    rows = db.session.query(List).filter(List.user_id == session["user_id"]).filter(List.item == ingredient).count()
    if rows != 0:
        # get the name of the current recipe from the user table in the db
        recipe_name = db.session.query(User).filter(User.id == session["user_id"]).first().current_recipe
        # query the db row for the recipe
        recipe = db.session.query(Recipe).filter(Recipe.name == recipe_name).filter(Recipe.user_id == session["user_id"]).first()
        # query the ingredients table for all ingredients for the current recipe
        ingredient_list = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe.id)
        # renders the template and sends the variables for use in the html/jinja
        prep_steps = recipe.prep_direction.split("\n")
        cook_steps = recipe.cook_direction.split("\n")
        note_steps = recipe.notes.split("\n")
        return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list, prep_steps=prep_steps, cook_steps=cook_steps, note_steps=note_steps, error="Item is already in your list")
    # add the item to the list table in the db
    data = List(user_id=session["user_id"], item=ingredient, note="", status="on")
    db.session.add(data)
    db.session.commit()
    # get the name of the current recipe from the user table in the db
    recipe_name = db.session.query(User).filter(User.id == session["user_id"]).first().current_recipe
    # query the db row for the recipe
    recipe = db.session.query(Recipe).filter(Recipe.name == recipe_name).filter(Recipe.user_id == session["user_id"]).first()
    # query the ingredients table for all ingredients for the current recipe
    ingredient_list = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe.id)
    # renders the template and sends the variables for use in the html/jinja
    prep_steps = recipe.prep_direction.split("\n")
    cook_steps = recipe.cook_direction.split("\n")
    note_steps = recipe.notes.split("\n")
    return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list, prep_steps=prep_steps, cook_steps=cook_steps, note_steps=note_steps, success="Item added to your list")


@app.route("/ingredient", methods=["POST"])
@login_required
def ingredient():
    # saves the form data in variables
    ingredient = request.form.get("ingredient")
    amount = request.form.get("ingredient_amount")
    recipe_id = request.form.get("ingredient_recipe")
    # query to see if the ingredient already exists for this user's recipe
    rows = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe_id).filter(Ingredients.item == ingredient).count()
    if rows != 0:
        # get the name of the current recipe from the user table in the db
        recipe_name = db.session.query(User).filter(User.id == session["user_id"]).first().current_recipe
        # query the db row for the recipe
        recipe = db.session.query(Recipe).filter(Recipe.name == recipe_name).filter(Recipe.user_id == session["user_id"]).first()
        # query the ingredients table for all ingredients for the current recipe
        ingredient_list = db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe.id)
        # renders the template and sends the variables for use in the html/jinja
        prep_steps = recipe.prep_direction.split("\n")
        cook_steps = recipe.cook_direction.split("\n")
        note_steps = recipe.notes.split("\n")
        return render_template("recipe.html", recipe_name=recipe_name, recipe=recipe, ingredient_list=ingredient_list, prep_steps=prep_steps, cook_steps=cook_steps, note_steps=note_steps, error="Ingredient already in recipe")

    # add the new ingredient row into the ingredients table in the db
    data = Ingredients(user_id=session["user_id"], recipe_id=recipe_id, amount=amount, item=ingredient)
    db.session.add(data)
    db.session.commit()
    return redirect("/recipe")


@app.route("/delete_ingredient", methods=["POST"])
@login_required
def delete_ingredient():
    # gets the recipe name and id from the hidden input connected to the html element
    recipe_id = request.form.get("recipe_id")
    recipe_ingredient = request.form.get("recipe_name")
    # 
    db.session.query(Ingredients).filter(Ingredients.user_id == session["user_id"]).filter(Ingredients.recipe_id == recipe_id).filter(Ingredients.item == recipe_ingredient).delete()
    db.session.commit()
    return redirect("/recipe")


@app.route("/prep", methods=["POST"])
@login_required
def prep():
    prep = request.form.get("prep")
    name = request.form.get("prep_recipe")
    db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).filter(Recipe.name == name).first().prep_direction = prep
    db.session.commit()
    return redirect("/recipe")


@app.route("/cook", methods=["POST"])
@login_required
def cook():
    cook = request.form.get("cook")
    name = request.form.get("cook_recipe")
    db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).filter(Recipe.name == name).first().cook_direction = cook
    db.session.commit()
    return redirect("/recipe")


@app.route("/note", methods=["POST"])
@login_required
def note():
    notes = request.form.get("note")
    name = request.form.get("note_recipe")
    db.session.query(Recipe).filter(Recipe.user_id == session["user_id"]).filter(Recipe.name == name).first().notes = notes
    db.session.commit()
    return redirect("/recipe")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user_id = session["user_id"]
    if request.method == "POST":
        password_hash = db.session.query(User).filter(User.id == user_id).first().hash
        # get all form values
        old = request.form.get("old_password")
        new = request.form.get("password")
        verify = request.form.get("confirmation")
        # ensure no form fields are empty
        if old == "" or new == "" or verify == "":
            username = db.session.query(User).filter(User.id == user_id).first().username
            return render_template("account.html", username=username, error="Please complete all fields")
        # verify that the old password is correct
        if not check_password_hash(password_hash, old):
            username = db.session.query(User).filter(User.id == user_id).first().username
            return render_template("account.html", username=username, error="Incorrect password")
        # verify that new password fields match
        if new != verify:
            username = db.session.query(User).filter(User.id == user_id).first().username
            return render_template("account.html", username=username, error="New passwords don't match")

        # create a hash for the new password
        new_hash = generate_password_hash(new)
        # update SQL table with new hash
        db.session.query(User).filter(User.id == user_id).first().hash = new_hash
        db.session.commit()
        username = db.session.query(User).filter(User.id == user_id).first().username
        return render_template("account.html", username=username, success="Success!")

    else:
        # get username
        username = db.session.query(User).filter(User.id == user_id).first().username
        return render_template("account.html", username=username)

