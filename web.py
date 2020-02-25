#!/usr/bin/env python

from flask import Flask, request, redirect, Response
from flask import render_template as rt
from generator import generator

app = Flask(__name__)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/rss", defaults={"username": ""})
@app.route("/rss/<username>")
def rss(username):
    if not username:
        return redirect("/")

    res = Response(generator.Generator(username, link=request.url).generate())
    res.headers["Content-Type"] = "application/xml"
    return res
