from flask import Flask, request, redirect, Response
from generator import generator
app = Flask(__name__)

@app.route('/', defaults={'username': ''})
@app.route('/<username>')
def index(username):
    if not username:
        return """
        <form method='post' action='/between'>
            <label for='username'>
                Username <input id='username' name='username'>
            </label>
            <input type='submit' value='Get Link'>
        </form>
        """

    link = 'localhost:5000/rss/' + username
    return '<a href="{link}">{link}</a>'.format(link=link)

@app.route('/between', methods=['POST'])
def between():
    return redirect('/' + request.form['username'])

@app.route('/rss', defaults={'username':''})
@app.route('/rss/<username>')
def rss(username):
    print(username)
    if not username:
        return redirect('/')

    res = Response(generator.Generator(username).generate())
    res.headers['Content-Type'] = 'application/xml'
    return res

