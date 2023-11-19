from flask import Flask, jsonify ,request
# db dependencies
import psycopg2
from flask_socketio import SocketIO
from flask_cors import CORS
import jwt
# env file dependencies
from psycopg2 import sql

from dotenv import load_dotenv
from os import environ
load_dotenv()

app = Flask(__name__, template_folder="../templates", static_folder="../static")
socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:5000")

CORS(app)

pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')
app.secret_key = environ.get('APP_SECRET_KEY')
conn = psycopg2.connect(environ.get('POSTGRES_URL'))


class User:

    def __init__(self, jwtToken):
        self.jwtToken = jwtToken
        self.username = self.get_current_user()
    
    def get_current_user(self):
        """ returns the current user's username from the payload of the JWT token thats passed from the userMetadata route"""
        payload = jwt.decode(self.jwtToken, private_key, algorithms="HS256")
        # make something that says no jwt found if payload is empty
        username = payload["user"]
        return username
    
    def verify_friendship(self, friend_to_check):
        # now we have to make a SQL query that will get us the messageID between both of these users
        cursor = conn.cursor()
        # checks if current user and searched user are friends. according to DB, user can either be friend1 (column is named username here) OR friend2 (column is named friend here).
        findMessageID = sql.SQL("""
            SELECT messageID
            FROM friendships
            WHERE (username = %(user_1)s AND friend = %(user_2)s) OR (username = %(user_2)s AND friend = %(user_1)s) 
        """)
        # we dont know exactly whether user_1 is the username or the friend on the SQL table
        cursor.execute(findMessageID, {"user_1": self.username, "user_2": friend_to_check})
        messageIDTuple = cursor.fetchone()

        # if the friendship between BOTH users exists (if messageID exists)
        if messageIDTuple is not None:
            messageID,= messageIDTuple
            return messageID
        else:
            raise Exception("Friendship does not exist.")

def get_chat_messages(messageID):
    """ GET ALL CHAT MESSAGES ACCORDING TO MESSAGEID- RETURNS A LIST """
    cursor = conn.cursor()
    view_all_messages = ("""
        SELECT username, current_message
        FROM messages
        WHERE messageID = %(messageID)s
        """)
        # passing in messageID 
    cursor.execute(view_all_messages, {"messageID": messageID})
    result = cursor.fetchall()
    print("RESULT: ", result)
    # storing all chat messages into a list
    chatMessages = []
        
    for username, chatMessage in result:
        print(username, chatMessage)
        chatMessages.append([username, chatMessage])

    return chatMessages


@socketio.on('connect')
def connect():
    print("SERVER connected")
    
@socketio.on('request_message')
def send_messages(data):
    try:
        jwt_token = data["data"]["jwt_token"]
        current_client = User(jwt_token)
        user_clicked = data["data"]["userFriend"]

        messageID = current_client.verify_friendship(user_clicked) # get messageID
        list_of_chat_messages = get_chat_messages(messageID) # get all the chat messages with the selected user.
        socketio.emit("send_room_messages", {"previous_room_messages": list_of_chat_messages, "room_id": messageID})
    except Exception as e:
        print(e)
    
        
@socketio.on('save_message_to_db')
def save_message_to_db(data):
    user = data["user"]
    message = data["message"]
    room_id = data['room_id']


    print('Received message:', message)
    cursor = conn.cursor()
    sql_insert_message_to_db = ("""
        INSERT INTO messages (username, current_message, messageid)
        VALUES (%s, %s, %s)
    """)
    
    new_message = (user, message, room_id)
    cursor.execute(sql_insert_message_to_db, new_message)
    conn.commit()
    socketio.emit("handle_new_message", {"user": user, "new_message": message})


if __name__ == '__main__': 
   socketio.run(app, port=5500)