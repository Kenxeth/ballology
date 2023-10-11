from flask import Flask, jsonify, request
from pymongo import MongoClient
import psycopg2
from psycopg2 import sql
import jwt
import pika
import json
# env file dependencies
from dotenv import load_dotenv
from os import environ
load_dotenv()

app = Flask(__name__, template_folder="../templates", static_folder="../static")

private_key = environ.get('SECRET_KEY')
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]

# makes sure user is authenticated

def get_user_attributes_from_db(username):
    # get description, pfp and friend_count from the SQL Table
    cursor = conn.cursor()
    getDescQuery = sql.SQL("""
        SELECT description
        FROM user_attributes
        WHERE username = %(username)s
    """)
    
    cursor.execute(getDescQuery, {"username": username})
    descTuple = cursor.fetchone()
    
    getPfpQuery = sql.SQL("""
        SELECT pfp
        FROM user_attributes
        WHERE username = %(username)s
    """)
    cursor.execute(getPfpQuery, {"username": username})
    pfpTuple = cursor.fetchone()

    getFriend_CountQuery = sql.SQL("""
        SELECT friend_count
        FROM user_attributes
        WHERE username = %(username)s
    """)

    cursor.execute(getFriend_CountQuery, {"username": username})
    getFriend_CountTuple = cursor.fetchone()
# when we do cursor.fetchone(), result is stored as a tuple. so we need to unpack the tuple
    desc, = descTuple
    pfp, = pfpTuple
    getFriend_Count, = getFriend_CountTuple

    return [desc, pfp, getFriend_Count]


def getCurrentUser(jwtToken):
    """ returns the current user's username from the payload of the JWT token thats passed from the userMetadata route"""
    payload = jwt.decode(jwtToken, private_key, algorithms="HS256")
    # make something that says no jwt found if payload is empty
    username = payload["user"]
    return username

# gets the current user for the friend request button
@app.route('/getCurrentUserForFriendRequest', methods=["POST"])
def getCurrentUserForFriendRequest():
    requestedInfo = request.get_json()
    get_jwtToken = requestedInfo["jwt"]
    userJWT = getCurrentUser(get_jwtToken)
    return jsonify({"current_user": userJWT})


@app.route('/userMetadata', methods=["POST"])
def profile():
    getRequest = request.get_json()
    
    user = getRequest["user"]

    username = user["username"]
    jwtToken = user["JWT"]
    # returns the current users username in order to change the layout of the users page- if its their account they can change their settings, if its not their account, they can try adding them as a friend   
    # check profile.html jinja templates for more information
    currentUser = getCurrentUser(jwtToken)

    # returns an array with desc, pfp and friend_count that is queried from a database
    user_attributes = get_user_attributes_from_db(username)
    desc = user_attributes[0]
    pfp = user_attributes[1]
    friend_count = user_attributes[2]

    return jsonify({"desc": desc, "pfp": pfp, "friend_count": friend_count, "currentUser": currentUser})

# changes user attributes (desc, profile picture, etc..)
@app.route("/changeUserProfileAttribute", methods=["POST"])
def changeUserProfileAttribute():
    """ change user data according to what client says """
    # get user changed description
    getResult = request.get_json()
    newUserDescription = getResult["data"]
    jwtToken = getResult["jwtToken"]

    username = getCurrentUser(jwtToken)

    cursor = conn.cursor()
    setNewDescQuery = sql.SQL("""
        UPDATE user_attributes
        SET description = %(description)s
        WHERE username = %(username)s
    """)
    # change user attributes to the new user attributes
    cursor.execute(setNewDescQuery, {"description": newUserDescription, "username": username})
    conn.commit()
    return newUserDescription


# currently requested by the friends microservice.
@app.route('/userFriendsData', methods=["POST"])
def userData():
    # grab JWT token from friends microservice and return a username and friend_count so that the server can show the client how many friends they have
    getJson = request.get_json()

    getUserJWT = getJson["jwt_token"]
    username = getCurrentUser(getUserJWT)
    userAttributes = get_user_attributes_from_db(username)
    friend_count = userAttributes[2]
    return jsonify({"username": username, "friend_count": friend_count})

if __name__ == '__main__': 
   app.run(port=5504)