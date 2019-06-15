#!/usr/bin/env python

from flask import Flask, request, redirect, Response
from flask import render_template as rt
from generator import generator
app = Flask(__name__)

@app.route('/', defaults={'username': ''})
@app.route('/<username>')
def index(username):
    return rt(
        'index.html',
        username=username,
        link=request.url_root + "rss/" + username
    )

@app.route('/between', methods=['POST'])
def between():
    return redirect('/' + request.form['username'])

@app.route('/rss', defaults={'username':''})
@app.route('/rss/<username>')
def rss(username):
    print(username)
    if not username:
        return redirect('/')

    res = Response(generator.Generator(username, link=request.url).generate())
    res.headers['Content-Type'] = 'application/xml'
    return res

