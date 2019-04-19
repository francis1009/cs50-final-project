import os

from cs50 import SQL
from operator import itemgetter
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///user.db")


@app.route("/")
def index():
    """Show homepage"""

    # Display index page
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Missing username!")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="Missing password!")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="Missing confirmation password!")

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="Password and confirmation do not match!")

        # Check if username inputted is unique
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get('username'))

        # Return error if username is taken
        if result:
            return render_template("error.html", message="Username is taken!")

        # Generate hash from password
        hash = generate_password_hash(request.form.get("password"))

        # Insert registered user into user table
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                   username=request.form.get('username'), hash=hash)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
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
            return render_template("error.html", message="Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="Must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", message="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/health")
def health():
    """Display health page"""

    # Render health.html page
    return render_template("health.html")


@app.route("/calorie")
def calorie():
    """Allow users to add calories with date"""

    # Render health.html page
    return render_template("calorie.html")


@app.route("/add", methods=["POST"])
def add():
    """Add calories with date to profile"""

    # Ensure username was submitted
    if not request.form.get("calorie"):
        return render_template("error.html", message="Must provide number of calories")

    # Ensure password was submitted
    elif not request.form.get("date"):
        return render_template("error.html", message="Must provide date")

    # Get user's ID
    user_id = session["user_id"]
    date = request.form.get("date")

    # Check if calories for date inputted exists
    exist = db.execute(f"SELECT * FROM calories WHERE id = {user_id} AND date = '{date}'")

    # Inserts new daily calorie intake if not exist
    if not exist:
        # Insert calorie with date into user's calorie profile
        db.execute("INSERT INTO calories (id, calorie, date) VALUES(:id, :calorie, :date)",
                   id=user_id, calorie=request.form.get("calorie"), date=request.form.get("date"))
        # Redirect user to user's profile page
        return redirect("/profile")

    # Update calorie intake of specific date inputted
    else:
        total = int(request.form.get("calorie")) + exist[0]["calorie"]
        db.execute(f"UPDATE calories SET calorie = '{total}' WHERE id = {user_id} AND date = '{date}'")
        # Redirect user to user's profile page
        return redirect("/profile")


@app.route("/calculator")
def calculator():
    """Display calculator page"""

    # Render calculator.html page
    return render_template("calculator.html")


@app.route("/bmi")
def bmi():
    """Display BMI Calculator"""

    # Render BMI Calculator page
    return render_template("bmi.html")


@app.route("/bmr")
def bmr():
    """Display BMR Calculator"""

    # Render BMR Calculator page
    return render_template("bmr.html")


@app.route("/whr")
def whr():
    """Display WHR Calculator"""

    # Render WHR Calculator page
    return render_template("whr.html")


@app.route("/profile")
@login_required
def profile():
    """Display user's profile"""

    # Get user's ID
    user_id = session["user_id"]

    # Obtain user's daily calorie intake
    calories_sort = db.execute(f"SELECT * FROM calories WHERE id = {user_id}")

    # Sort calorie intake in reverse order of date
    calories = sorted(calories_sort, key=itemgetter('date'), reverse=True)

    # Display profile page
    return render_template("profile.html", calories=calories)


@app.route("/delete", methods=["POST"])
def delete():
    """Delete calories with date from profile"""

    # Get user's ID
    user_id = session["user_id"]

    # Obtain date of row to be deleted
    date = request.form.get("date")

    # Delete row
    db.execute(f"DELETE FROM calories WHERE id = '{user_id}' AND date = '{date}'")

    return redirect("/profile")


@app.route("/changeuser", methods=["GET", "POST"])
@login_required
def changeuser():
    """Allow user to change username"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure new username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Missing username!")

        # Check if username inputted is unique
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get('username'))

        # Return error if username is taken
        if result:
            return render_template("error.html", message="Username is taken!")

        # Get user's ID
        user_id = session["user_id"]

        # Obtain user's new username
        username = request.form.get("username")

        # Update user's username
        db.execute(f"UPDATE users SET username = '{username}' WHERE id = {user_id}")

        # Query database for user
        rows = db.execute(f"SELECT * FROM users WHERE id = {user_id}")

        # Remember which user has logged in
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changeuser.html")


@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    """Allow user to change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure old password was submitted
        if not request.form.get("oldpassword"):
            return render_template("error.html", message="Missing old password!")

        # Ensure new password was submitted
        elif not request.form.get("newpassword"):
            return render_template("error.html", message="Missing new password!")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="Missing confirmation password!")

        # Ensure password and confirmation match
        elif request.form.get("newpassword") != request.form.get("confirmation"):
            return render_template("error.html", message="Password and confirmation do not match!")

        # Get user's ID
        user_id = session["user_id"]

        # Query database for user
        rows = db.execute(f"SELECT * FROM users WHERE id = {user_id}")

        # Ensure old password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("oldpassword")):
            return render_template("error.html", message="Old password does not match.")

        # Generate hash from new password
        hash = generate_password_hash(request.form.get("newpassword"))

        # Update user's password
        db.execute(f"UPDATE users SET hash = '{hash}' WHERE id = '{user_id}'")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepass.html")