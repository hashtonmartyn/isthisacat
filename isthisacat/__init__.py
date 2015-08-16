'''
Created on Aug 6, 2015

@author: hashtonmartyn
'''
from flask import Flask, render_template, request, abort, g, redirect
from flask_wtf.csrf import CsrfProtect
import os
import sqlite3
from contextlib import closing

DATABASE_PATH_KEY = "DATABASE_PATH"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config[DATABASE_PATH_KEY] = os.path.abspath(os.path.join(os.path.realpath(__file__),
                                                             os.pardir,
                                                             os.pardir,
                                                             "database.db"))
csrf = CsrfProtect(app)

def connect_to_database():
    return sqlite3.connect(app.config[DATABASE_PATH_KEY])

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = connect_to_database()
    return db
        
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
        
def init_db():
    with closing(connect_to_database()) as db:
        head, tail = os.path.split(os.path.realpath(__file__))
        schema_path = os.path.join(head,
                                   "schema.sql")
        with app.open_resource(schema_path, mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def _get_votes(iscat):
    db = get_db()
    cursor = db.execute("SELECT COUNT(*) FROM votes where iscat=='%s'" % iscat)
    num_votes = cursor.fetchall()
    cursor.close()    
    return int(num_votes[0][0])
    
def get_yes_votes():
    return _get_votes("TRUE")

def get_no_votes():
    return _get_votes("FALSE")

@app.route("/votes/yes")
def yes_votes():
    """
    Test interface, shouldn't be exposed in production
    """
    if app.config.get("TESTING") is True:
        return str(get_yes_votes())
    abort(404)
        
@app.route("/votes/no")
def no_votes():
    """
    Test interface, shouldn't be exposed in production
    """
    if app.config.get("TESTING") is True:
        return str(get_no_votes())
    abort(404)

@app.route("/")
def index():
    if request.cookies.get("voted") is None:
        return render_template("index_no_vote.html")
    else:
        num_yes_votes = get_yes_votes()
        num_no_votes = get_no_votes()
        return render_template("index_already_voted.html",
                               num_yes_votes=num_yes_votes,
                               num_no_votes=num_no_votes)

@app.route("/vote", methods=["POST"])
def vote():
    if request.form.get("iscat") not in ("TRUE", "FALSE"):
        abort(400)
    db = get_db()
    db.execute("INSERT INTO votes (iscat) Values ('%s')" % request.form["iscat"])
    db.commit()
    response = app.make_response(redirect("/"))
    response.set_cookie("voted")
    return response

@csrf.error_handler
def csrf_error(reason):
    request.csrf_error_reason = reason
    abort(400)
    
@app.errorhandler(400)
def error_code_400(error):
    try:
        error = request.csrf_error_reason
    except AttributeError:
        # If it's not a CSRF error then it's just a normal error
        pass
    return render_template("csrf_error.html", reason=error), 400
    
if __name__ == "__main__":
    app.config[DATABASE_PATH_KEY] = "database.db"
    init_db()
    app.run(host="0.0.0.0", port=3000, debug=True)