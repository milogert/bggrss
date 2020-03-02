#!/usr/bin/env python

from flask import Flask, request, redirect, Response
from flask import render_template as rt
from icecream import ic

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

    ic(request.args)
    res = Response(
        generator.Generator(
            username,
            link=request.url,
            feed_debugging=request.args.get("debug", default=False, type=bool),
        ).generate()
    )
    res.headers["Content-Type"] = "application/xml"
    return res
