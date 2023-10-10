from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
# db dependencies
import requests
from pymongo import MongoClient
import psycopg2
# jwt token dependencies
import jwt

from flask_socketio import SocketIO, emit

import pika

# env file dependencies
from dotenv import load_dotenv
from os import environ
load_dotenv()
app = Flask(__name__, static_folder="../static", template_folder="../templates")
socketio = SocketIO(app)
bcrypt = Bcrypt(app)

private_key = environ.get('SECRET_KEY')
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]


@app.route('/friends', methods=["POST"])
def friends(): 
#    grabbing jwt passing it on to profile microservice to find out what the current users friends count and username is
   
   getJson = request.get_json()
   userJWT = getJson["jwt_token"]
   response = requests.post('http://127.0.0.1:5504/userFriendsData', json={"jwt_token": userJWT}, headers={"Content-Type": "application/json"})
   
   
   if response.status_code == 204:
      print("No content returned.")
   elif response.status_code == 200:
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
      print("Invalid JSON in the response.")
   else:
       print(f"Error: {response.reason}")
  
   return jsonify({"friend_count": data["friend_count"], "username": data["username"]})


@app.route('/sendFriendRequest', methods=["POST"])
def sendFriendRequest():
    # get requested user and get the current user logged in (or the requester) to make a friend request
    getResultFromMain = request.get_json()
    requested_user = getResultFromMain["requested_user"]
    userJWT = getResultFromMain["JWT"]
    requester = getCurrentUser(userJWT)

    makeFriendRequest(requester, requested_user)
    # make error handling here
    return "lala"
 

def getCurrentUser(jwtToken):
    """ returns the current user's username from the payload of the JWT token thats passed from the userMetadata route"""
    payload = jwt.decode(jwtToken, private_key, algorithms="HS256")
    # make something that says no jwt found if payload is empty
    username = payload["user"]
    return username



def makeFriendRequest(requester, requested_user):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
    channel = connection.channel()
    channel.exchange_declare(exchange="direct_log", exchange_type="direct")
    channel.queue_declare("friend_request")
    # bind the queue with a routing_key so that messages go to that routing key; direct exchange
    channel.queue_bind(exchange='direct_log', queue='friend_request', routing_key=f'{requested_user}')
    message = f"Hello, {requested_user}. {requester} wants to be your friend."
    channel.basic_publish(exchange='direct_log', routing_key= f'{requested_user}', body=message)
    channel.basic_consume(queue='friend_request', on_message_callback=callback, auto_ack=True)
    connection.close()







# AFTER THAT MAKE SURE THAT WHENEVER THE USER CLICKS THE BUTTON,
   # A FRIEND REQUEST IS SENT TO THE USERS BROWSER

   # IF THAT FRIEND REQUEST IS ACCEPTED THEN A FRIENDSHIP IS FORMED.
   # UPDATE THE SQL DATABASE SO IT IS USERNAME: FRIEND.

   # THIS WAY WE CAN MAKE A FOR FRIENDS IN FRIEND LOOP IN JINJA TEMPLATE TO MAKE A 
   # CONTAINER FOR EVERY FRIEND SO THAT WHENEVER A USER GOES TO /FRIENDS THEY CAN SEE ALL THEIR FRIENDS

   # ONCE U FIGURE THAT, A FRIEND REQUEST IS MADE AND WE HAVE TO REUPDATE THE DATABASE.
   # REUPDATE THE DATABASE THROUGH PGADMIN 4. 
   # WE HAVE TO SET THE VALUE OF FRIENDS COLUMN IN THE USER_ATTRIBUTES TABLE TO THE COUNT OF THE FRIENDS TABLE

if __name__ == '__main__': 
   app.run(port=5501)