

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from flask_socketio import SocketIO, emit

from helpers import apology, login_required

from api import related_search, query_search

import csv


# Configure application
app = Flask(__name__)

# setup socketio
socketio = SocketIO(app)

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


@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET: Show the main page
    POST: performs a youtube api search and display results
    """

    return render_template("index.html")



@app.route("/navegar", methods=["GET", "POST"])
def navegar():
    """
    GET: Show the query page
    POST: performs a youtube api search and display results
    """

    # GET request
    if request.method == "GET":
        return render_template("navegar.html")

    # POST request
    elif request.method == "POST":


        # get search str
        query = request.form.get("query")
        seed = request.form.get("seed-mode")

        #videos = ytnav(query, seed)

        #for video in videos:
            #print(video)

        if request.form.get("seed-mode") == True:
            videos = related_search(query)
        else:
            videos = query_search(query)


        # render the page
        return render_template("results.html", videos=videos)

@app.route("/coletar", methods=["GET", "POST"])
def coletar():
    """
    GET: Show the query page
    POST: performs a youtube api search and display results
    """

    # GET request
    if request.method == "GET":
        return render_template("coletar.html")

    # POST request
    elif request.method == "POST":


        # get search str
        query = request.form.get("query")
        seed = request.form.get("seed-mode")
        profundidade = request.form.get("profundidade")

        #videos = ytcollect(query, seed) # adicionar a profundidade depois
        ########################################################################

        # Faz um query search, e para cada resultado faz uma busca de video relacionados
        videos = query_search(query)
        final_video_list += videos

        for video in videos:
            videos2 = related_search(video[2])
            final_video_list += videos2

        #return final_video_list


        ########################################################################

        # render the page
        return render_template("results.html", videos=final_video_list)


@app.route("/analisar") #, methods=["GET", "POST"]
def analisar():
    """
    Cria uma visualização usando os dados coletados
    """


    # render the page
    return render_template("analisar.html")


@app.route("/results/<id>", methods=["GET", "POST"])
def results(id):
    """
    Receives a youtube video id, and get it's related videos
    the related videos are displayed to the user
    """

    videos = related_search(id)

    return render_template("results.html", videos=videos)

@socketio.on('get_nodes')
def get_nodes():
    '''Sends the nodes data to the user'''

    # fazer a leitura a partir do arquivo csv????????
    nodes = []

    with open('static/nodes.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',') # quotechar='|'
        for row in reader:
            if row[0] != 'related_video_id':
                line = [row[0], row[1]]
                nodes.append(line)

    emit('get_nodes', nodes)


@socketio.on('get_edges')
def get_edges():
    '''Sends the edges data to the user'''

    # fazer a leitura a partir do arquivo csv????????
    edges = []

    with open('static/edges.csv', 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',') # quotechar='|'
        for row2 in reader2:
            if row2[0] != 'source':
                line2 = [row2[0], row2[2]]
                edges.append(line2)

    emit('get_edges', edges)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
