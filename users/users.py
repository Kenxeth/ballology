from flask import Flask, render_template, request, make_response, redirect, url_for, flash
from flask_bcrypt import Bcrypt
# db dependencies
from pymongo import MongoClient
import psycopg2
# jwt token dependencies
import jwt
from functools import wraps

from flask_socketio import SocketIO, emit
import traceback

# env file dependencies
from dotenv import load_dotenv
from os import environ

app = Flask(__name__)
socketio = SocketIO(app)
bcrypt = Bcrypt(app)



if __name__ == '__main__': 
   socketio.run(app)