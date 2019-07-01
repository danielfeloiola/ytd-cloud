import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

import requests
import json

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

DEVELOPER_KEY = os.environ['API']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Configure application
app = Flask(__name__)

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
#Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///ytdata.db")


@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET: Show the main page
    POST: performs a youtube api search and display results
    """

    if request.method == "POST":

        # lists for "storage"
        videos = []
        channels = []
        playlists = []

        # get search str
        query = request.form.get("query")

        #import the search function
        #from test import youtube_search
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

        # Call the search.list method to retrieve results matching the specified
        # query term.
        search_response = youtube.search().list(q=query, part="id,snippet").execute()

        # Add each result to the appropriate list, and then display the lists of
        # matching videos, channels, and playlists.
        for search_result in search_response.get("items", []):

            # usa apenas os vídeos recomendados
            if search_result["id"]["kind"] == "youtube#video":
                list = [search_result["snippet"]["title"],
                        search_result["id"]["videoId"],
                        search_result["snippet"]["channelTitle"],
                        search_result["snippet"]["channelId"],
                        search_result["snippet"]["publishedAt"],
                        search_result["snippet"]["description"],
                        search_result["snippet"]["thumbnails"]["default"]["url"],
                        "video"
                        ]
                videos.append(list)




        return render_template("results.html", videos=videos)

    # GET request
    elif request.method == "GET":
        return render_template("index.html")


@app.route("/results/<id>", methods=["GET", "POST"])
def results(id):
    """
    Receives a youtube video id, and get it's related videos
    the related videos are displayed to the user
    """

    # lists for "storage"
    videos = []
    channels = []
    playlists = []

    # get the video id
    video_id = id

    # setup api
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    #search_response = youtube.search().list(q=query, part="id,snippet").execute()
    res = youtube.search().list(relatedToVideoId=video_id,
                                part="id,snippet",
                                maxResults=20,
                                type='video').execute()

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in res.get("items", []):

        # usa apenas os vídeos recomendados
        if search_result["id"]["kind"] == "youtube#video":
            list = [search_result["snippet"]["title"],
                    search_result["id"]["videoId"],
                    search_result["snippet"]["channelTitle"],
                    search_result["snippet"]["channelId"],
                    search_result["snippet"]["publishedAt"],
                    search_result["snippet"]["description"],
                    search_result["snippet"]["thumbnails"]["default"]["url"],
                    "video"
                    ]
            videos.append(list)


    return render_template("results.html", videos=videos)



############




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
