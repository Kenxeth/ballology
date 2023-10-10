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

# sends the users 
@app.route('/sendUserFriendRequest', methods=["POST"])
def sendUserFriendRequest():

    getResult = request.get_json()
    get_JWT = getResult["JWT"]
    User_Requester = getCurrentUser(get_JWT)
    requested_user = getResult["requested_user"]
    try:
        # put the user_requester and requested user in a stack so that 
        # when 
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
        channel = connection.channel()
        channel.queue_declare(queue="friend_request")
        channel.basic_publish(exchange='',
                        routing_key='friend_request',
                        body=json.dumps({"user_requester": User_Requester, "requested_user": requested_user}))
        connection.close()
    except Exception as e:
        return jsonify({"message": "failed"})
    return jsonify({"message": "success"})


def send_friend_request(sender, recipient, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a direct exchange
    channel.exchange_declare(exchange='friend_requests', exchange_type='direct')

    # Declare a queue for the recipient user
    channel.queue_declare(queue=recipient)
    
    # Bind the queue to the exchange with the recipient user as the routing key
    channel.queue_bind(exchange='friend_requests', queue=recipient, routing_key=recipient)

    # Send the friend request message to the exchange with the recipient user as the routing key
    channel.basic_publish(exchange='friend_requests', routing_key=recipient, body=message)

    connection.close()




if __name__ == '__main__': 
   app.run(port=5504)