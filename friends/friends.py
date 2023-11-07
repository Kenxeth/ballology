from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
# db dependencies
import requests
from pymongo import MongoClient
import psycopg2
# jwt token dependencies
import jwt

import secrets
import string

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

from psycopg2 import sql

private_key = environ.get('SECRET_KEY')
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]

# default function. whenever the user visits the friends page. this function runs and checks if
# any friend requests have been sent to the user, and shows all of the currrent users current friends.
@app.route('/friends', methods=["POST"])
def friends(): 
#    grabbing jwt passing it on to profile microservice to find out what the current users friends count and username is
   
   getJson = request.get_json()
   userJWT = getJson["jwt_token"]
#    GRABBING USER FRIEND COUNT + USERNAME
   response = requests.post('http://127.0.0.1:5504/userFriendsData', json={"jwt_token": userJWT}, headers={"Content-Type": "application/json"})
   

   if response.status_code == 204:
      print("No content returned.")
   elif response.status_code == 200:
    try:
        # data has been passed from profile microservice to display user metadata
        data = response.json()
        
        username = data["username"]

        # GRAB ALL USERS CURRENT FRIENDS
        listofCurrentUsersFriends = getUsersCurrentFriends(username)

        # GRAB ANY FRIEND REQUEST THAT THE USER MIGHT HAVE.
        getCurrentFriendRequests = handleFriendRequest(userJWT)
        currentFriendRequest = getCurrentFriendRequests["friend_request_status"]

    except requests.exceptions.JSONDecodeError:
      print("Invalid JSON in the response.")
   else:
       print(f"Error: {response.reason}")
  
   return jsonify({"friend_count": data["friend_count"], "username": username, "currentFriendRequest": currentFriendRequest, "listOfCurrentUsersFriends": listofCurrentUsersFriends})

# makes a list of all the users current friend
def getUsersCurrentFriends(user):
    cursor = conn.cursor()
    # checks how many friends current user has. according to DB, user can either be friend1 (column is named username here) OR friend2 (column is named friend here).
    getFriend_CountQuery = sql.SQL("""
        SELECT username, friend
        FROM friendships
        WHERE (username = %(username)s) OR (friend = %(username)s)
    """)

    cursor.execute(getFriend_CountQuery, {"username": user})
    # returns a list of tuples with all the RELATIONSHIPS with the CURRENT user
    allRelationshipsWithCurrentUser = cursor.fetchall()

    #  grab each tuple and append to list.
    list_of_users = []
    for friend1, friend2 in allRelationshipsWithCurrentUser:
        # made the DB so that the user can either be friend1 or friend2. therefore we have to figure out which friend the user is so we dont put that in the friends list
        # because a user CANT be their own friend
        
        # ex: if user is friend1, append the other user (the friend) onto the list aka FRIEND2
      
       if friend1 != user:
          list_of_users.append(friend1)
       elif friend2 != user:
          list_of_users.append(friend2)
    
    return list_of_users

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
       return {"friend_request_status": body}
    

    # listen to messages in the current_user queue- aka server is going to be listening to the current user logged in friend req.
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
    channel = connection.channel()
    for method_frame, properties, body in channel.consume(queue=current_user, auto_ack=True, inactivity_timeout= 0.5):
        if method_frame:
            # originally body is in bytes
            decoded_body = body.decode('utf-8')
            return callback(None, method_frame, properties, decoded_body)
        else:
           connection.close()
           return {"friend_request_status": "No Friend Request Sent."}
# accepts user friend requests
@app.route('/acceptFriendRequest', methods=["POST"])
def acceptFriendRequest():
    getFriendRequestMessage = request.get_json()
  
    # get the friend request message
    friendRequestMessage = getFriendRequestMessage["friend_request_message"]
    # split the message into an array so we can find out who the requester and the requested is
    friendRequestMessageList = list(friendRequestMessage.split(" "))
    requested = friendRequestMessageList[1]
    requester = friendRequestMessageList[2]

    # add requester and requested to the friendship SQL DB
    cursor = conn.cursor()

    # message_id is a unique id for every friendship that is going to be used for DM's.
    message_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
              for i in range(24))
    

    addFriendRelationshipTo = sql.SQL("""
        INSERT INTO friendships (username, friend, messageid)
        VALUES (%(username)s , %(friend)s, %(message_id)s)
    """)

    # friendship relationships require BOTH users to be friends
    cursor.execute(addFriendRelationshipTo, {"username": requester, "friend": requested, "message_id": message_id})
    conn.commit()
    
    return jsonify({"who knows": "asdplsa"})


if __name__ == '__main__': 
   app.run(port=5501)