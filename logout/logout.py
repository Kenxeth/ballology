import flask
from flask import Flask, render_template, request, make_response, redirect, url_for, flash
from flask_bcrypt import Bcrypt
# db dependencies

from functools import wraps
import traceback

# env file dependencies
from dotenv import load_dotenv
from os import environ


app = Flask(__name__, template_folder="../templates")
bcrypt = Bcrypt(app)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if flask.request.method == "GET":
       return render_template('logout.html')

    response = make_response(redirect('http://127.0.0.1:5502/login'))
    response.set_cookie('JWT', '', expires=0)
    response.set_cookie("username", '', expires=0)
    return response


if __name__ == '__main__': 
   app.run(port=5503)