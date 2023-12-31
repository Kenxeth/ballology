# dependencies
from flask import Flask, render_template, request, make_response, jsonify, redirect, url_for, flash
import flask
from flask_bcrypt import Bcrypt
import requests
# db dependencies
from pymongo import MongoClient
import psycopg2
# jwt token dependencies
import jwt
from functools import wraps

from flask_socketio import SocketIO, emit
import traceback

import pika

# env file dependencies
from dotenv import load_dotenv
from os import environ
load_dotenv()


# set up/boiler plate code
cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]

app = Flask(__name__)
bcrypt = Bcrypt(app)

# load env variables to use
pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')
app.secret_key = environ.get('APP_SECRET_KEY')

# SQL connection
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

class Person:
  def __init__(self, username, password):
    self.username = username
    self.password = password

# flask middleware to authenticate users
def check_for_token(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        try:
            JWT = request.cookies.get('JWT')
            if 'JWT' in request.cookies:
                decodedJWT = jwt.decode(JWT, private_key, algorithms=["HS256"])
                if decodedJWT == None:
                    raise jwt.exceptions.InvalidTokenError
            else:
                raise jwt.exceptions.DecodeError
        except jwt.exceptions.DecodeError:
            print("Sorry, not validated.")
            return redirect('http://127.0.0.1:5000/login')
        except jwt.exceptions.InvalidTokenError:
            print("Sorry token invalid.")
            return redirect('http://127.0.0.1:5000/login')
        except Exception as e:
            print('err', e)
            print(traceback.format_exc())
            return redirect('http://127.0.0.1:5000/login')
        return func(*args, **kwargs)
    return inner_func


@app.route('/register', methods=["GET", "POST"])
def register():
   try:
      if flask.request.method == "GET":
        if request.cookies.get('username') is not None:
            username = request.cookies.get('username')
            return redirect(f"http://127.0.0.1:5000/user/{username}")
        return render_template('register.html')
      username = request.form.get('username')
      password = request.form.get('password')
      newPerson = Person(username, password)
      responseFromRegister = requests.post("http://127.0.0.1:5505/registerUser", json={'user': newPerson.__dict__}, headers = {'Content-Type': 'application/json'})
      # grab result from the request we sent to the microservice
      message = responseFromRegister.json() 
      flash(message["message"])
   except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"message": "Sorry something went wrong. Please try again."})
   
   return redirect(url_for('register'))
   
   
@app.route('/login', methods=["GET", "POST"])
def login():
   try:
      if flask.request.method == "GET":
        if request.cookies.get('username') is not None:
            username = request.cookies.get('username')
            url = f"http://127.0.0.1:5000/user/{username}"
            return redirect(url)
        return render_template('login.html')
   # if its a POST request...
      username = request.form.get('username')
      password = request.form.get('password')
      newPerson = Person(username, password)
      responseFromLogin = requests.post('http://127.0.0.1:5502/loginUser', json={"user": newPerson.__dict__}, headers={'Content-Type': 'application/json'})
      # grab result from the request we sent to the microservice
      responseDictFromLogin = responseFromLogin.json() 
      # checks to see what is in the dictionary: message or JWT token
      # JWT Token auth is checked by nginx
      if "message" in responseDictFromLogin:
          flash(responseDictFromLogin["message"])
      elif "JWT" in responseDictFromLogin:
         resp = make_response(redirect('login'))
         resp.set_cookie('username', responseDictFromLogin["username"], max_age= 10000)
         resp.set_cookie('JWT', responseDictFromLogin["JWT"], max_age=10000)
         return resp
   except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"message": "Sorry something went wrong. Please try again."})
   return redirect(url_for('login'))

@app.route('/')
@app.route('/user/<user>', methods= ["GET", "POST"])
@check_for_token
def profile(user):
    # if the user is trying to grab a profile (either theirs or not theirs)
    if flask.request.method == "GET":
        findCorrectUser = collection.find_one({'username': user})
        if findCorrectUser is None: 
            return render_template('404.html'), 404
        
        # sending jwt token and user so we can figure out the users metadata from the DB (profile.py deals with that)
        result = requests.post('http://127.0.0.1:5504/userMetadata', json={"JWT": request.cookies.get("JWT"), "userBeingLookedUp": user}, headers={'Content-Type': 'application/json'})
        
        userMetadata = result.json()
            # passing user metadata into jinja template for displaying purposes
        currentUser = userMetadata["currentUser"]
        desc = userMetadata["desc"]
        friend_count = userMetadata["friend_count"]
        pfp = userMetadata["pfp"] 
        is_other_user_friend = userMetadata["is_other_user_friend"]

        return render_template('profile.html', currentUser=currentUser, user=user, desc=desc, pfp=pfp, friend_count=friend_count, is_other_user_friend=is_other_user_friend)
    # if a user is trying to send a friend request to another user  (clicks on the friend request button)...
    elif flask.request.method == "POST":
        return "lala"
        
   
@app.route('/changeUserData', methods=["POST"])
@check_for_token
def changeUserData():
   data = request.form.get("changed_description")
   # send data + JWT to microservice so it can change user metadata
   requests.post('http://127.0.0.1:5504/changeUserProfileAttribute', json={"data": data, "jwtToken": request.cookies.get("JWT")}, headers={'Content-Type': 'application/json'})
   username = request.cookies.get("username")
   return redirect(f"http://127.0.0.1:5000/user/{username}")

@app.route('/friends', methods=["GET"])
@check_for_token
def friends():
        result = requests.post('http://127.0.0.1:5501/friends', json={"jwt_token": request.cookies.get("JWT")}, headers={'Content-Type': 'application/json'})
        getUserJson = result.json()

        return render_template('friends.html', friend_count=getUserJson["friend_count"], user=getUserJson["username"], currentFriendRequest= getUserJson["currentFriendRequest"], listOfCurrentUsersFriends=getUserJson["listOfCurrentUsersFriends"])

@app.route('/sendFriendRequest', methods=["POST"])
@check_for_token
def sendFriendRequest():
    # in async comm. the server has to send the message to the queue instead
        # and the microservice retrieves this message and does something with it
        
        requester = request.form.get('currentUser')
        requested = request.form.get('user')


        # SEND A FRIEND REQUEST VIA RABBITMQ (SENDING A MESSAGE TO THE QUEUE VIA DIRECT EXCHANGE)

        # REQUESTED USER IS user in this case (just grabbing the user from url)
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
        channel = connection.channel()
        # declare a exchange 
        channel.exchange_declare(exchange="direct_log", exchange_type="direct")
        # BINDING the queue with routing_key (requested that got requested), so that if the user 
        # that got requested gets a friend request/message... the server can take care of doing everything else
        channel.queue_bind(exchange='direct_log', queue=requested, routing_key=f'{requested}')
        message = f"Hello {requested} {requester} wants to be your friend. Do you want to be friends?"
        channel.basic_publish(exchange='direct_log', routing_key= f'{requested}', body=message)
        connection.close()
        return redirect(f"http://127.0.0.1:5000/user/{requested}")

@app.route('/acceptFriendRequest', methods=["POST"])
@check_for_token
def acceptFriendRequest():
    # YOU HAVE AN ERROR GOING ON, WHENEVER YOU TRY TO ADD THE FRIEND AFTER REQUEST
    # ERROR APPEARS

    # YOU ARE CURRENTLY TRYING TO DELETE THE DOCUMENTS IN SQL TO RESET FRIEND REQUESTS TO
    # TRY THIS AGAIN.
    
    friendRequestMessage = request.form.get('currentFriendRequest')

    requests.post('http://127.0.0.1:5501/acceptFriendRequest', json={"friend_request_message": friendRequestMessage}, headers={'Content-Type': 'application/json'})
    return redirect('http://127.0.0.1:5000/friends')

@app.route('/declineFriendRequest', methods=["POST"])
@check_for_token
def declineFriendRequest():
    return redirect('http://127.0.0.1:5000/friends')

@app.route('/getCurrentFriends', methods=["POST"])
@check_for_token
def getCurrentFriends():
    request.get_json()
    response = requests.post('http://127.0.0.1:5501/getCurrentFriends', json={"jwt_token": request.cookies.get("JWT")}, headers={"Content-Type": "application/json"})
    result = response.json()
    # figure out how to pass through current_clients username so we can use it in chat.js
    # and say username: this is my message and boom
    return jsonify({"current_client": result["current_client"], "jwt": request.cookies.get("JWT"), "list_of_friends": result["list_of_friends"]})

@app.route('/test')
def test():
    return render_template("test.html")


if __name__ == '__main__': 
   app.run(debug=False)