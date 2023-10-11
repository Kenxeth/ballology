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
import json
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
        # data has been passed from profile microservice to display user metadata
        data = response.json()
        
        getCurrentFriendRequests = handleFriendRequest(userJWT)
        currentFriendRequest = getCurrentFriendRequests["friend_request_status"]
        print("what we've all been waiting for: ", currentFriendRequest)
        # 2) /HANDLEFR SHOULD GIVE THIS INFORMATION TO /FRIENDS
        # 3) /FRIENDS SHOULD BE ABLE TO DISPLAY THIS MESSAGE HOPEFULLY ON THE USER BROWSER
        # WITH JINJA TEMPLATE

    except requests.exceptions.JSONDecodeError:
      print("Invalid JSON in the response.")
   else:
       print(f"Error: {response.reason}")
  
   return jsonify({"friend_count": data["friend_count"], "username": data["username"]})

# gets the current user according to JWT token
def getCurrentUser(jwtToken):
    """ returns the current user's username from the payload of the JWT token thats passed from the userMetadata route"""
    payload = jwt.decode(jwtToken, private_key, algorithms="HS256")
    # make something that says no jwt found if payload is empty
    username = payload["user"]
    return username

# listens for user friend requests according to the current user logged in.
def handleFriendRequest(jwtToken):
    
    current_user = getCurrentUser(jwtToken)
    
    # if a message appears in the queue, this callback will be called.
    def callback(ch,method,properties,body):
       connection.close()
       print(type(body))
       return {"friend_request_status": body}
    

    # listen to messages in the current_user queue- aka server is going to be listening to the current user logged in friend req.
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
    channel = connection.channel()
    for method_frame, properties, body in channel.consume(queue=current_user, auto_ack=True, inactivity_timeout= 1):
        if method_frame:
            # originally body is in bytes
            decoded_body = body.decode('utf-8')
            return callback(None, method_frame, properties, decoded_body)
        else:
           return {"friend_request_status": "No Friend Request Sent"}




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