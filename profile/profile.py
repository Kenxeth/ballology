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

class User:
    def __init__(self, jwt):
        self.jwtToken = jwt
        self.username = self.get_current_user()
    
    def get_current_user(self):
        """ returns the current user's username from the payload of the JWT token thats passed from the userMetadata route"""
        
        payload = jwt.decode(self.jwtToken, private_key, algorithms="HS256")
        # make something that says no jwt found if payload is empty
        username = payload["user"]
        return username
    
    def get_user_attributes_from_db(self):
        """
            Getting attributes from SQL db so that we can display it on to the screen of the client.

            search_attribute_list (list): list of attributes (columns) to search for in the db- we need the description, pfp and friend_count from every user
            attribute_list (list) : list of user attributes that came back from the db
        """
        search_attribute_list = ["description", "pfp", "friend_count"]
        attribute_list = []
        for attribute in search_attribute_list:
            cursor = conn.cursor()
            query = sql.SQL(f"""
                SELECT {attribute}
                FROM user_attributes
                WHERE username = %(username)s
            """)
        
            cursor.execute(query, {"username": self.username})
            tuple = cursor.fetchone()
            attribute, = tuple
            attribute_list.append(attribute,)
        
        return attribute_list

    def change_user_attribute(self, new_description):
        cursor = conn.cursor()
        set_new_desc_query = sql.SQL("""
            UPDATE user_attributes
            SET description = %(description)s
            WHERE username = %(username)s
        """)
        # change user attributes to the new user attributes
        cursor.execute(set_new_desc_query, {"description": new_description, "username": self.username})
        conn.commit()
        return new_description

    def check_relationship(self, other_user):
        """
        Check whether the current user and a random other user are friends.

        other_user(string) = the other user
        """
        is_user_friend = True
        
        # making sure that the user being looked up is not the user logged in 
        if self.username != other_user:
            cursor = conn.cursor()
            check_friend_relationship = sql.SQL("""
                SELECT 1
                FROM friendships
                WHERE (username = %(username)s AND friend = %(friend)s) OR (username= %(friend)s AND friend = %(username)s);
            """)
            # user can be BOTH a user AND friend 
            
            cursor.execute(check_friend_relationship, {"username": self.username, "friend": other_user})
            checking_CurrentUser_And_User_LookedUp_RelationshipTuple = cursor.fetchone()
            
            if checking_CurrentUser_And_User_LookedUp_RelationshipTuple is None:
                # if user_friend false, then the user looked up is NOT a friend. meaning that the current user logged in can send a friend request.
                is_user_friend = False
            else:
                # user logged in IS a friend; can't send a friend req to someone who's already considered a friend.
                is_user_friend = True
        
        return is_user_friend


@app.route('/getCurrentUserForFriendRequest', methods=["POST"])
def getCurrentUserForFriendRequest():
    requestedInfo = request.get_json()
    get_jwtToken = requestedInfo["jwt"]
    userJWT = getCurrentUser(get_jwtToken)
    return jsonify({"current_user": userJWT})

# put user metadata on to the profile.html
@app.route('/userMetadata', methods=["POST"])
def profile():
    get_request = request.get_json()
    
    jwt_token = get_request["JWT"]
    user_being_looked_up = get_request["userBeingLookedUp"]

    current_client = User(jwt_token)
    current_clients_username = current_client.username
    attribute_list = current_client.get_user_attributes_from_db()    
    is_other_user_friend = current_client.check_relationship(user_being_looked_up)
    
    return jsonify({"desc": attribute_list[0], "pfp": attribute_list[1], "friend_count": attribute_list[2], "currentUser": current_clients_username, "is_other_user_friend": is_other_user_friend})
    
# changes user attributes (desc, profile picture, etc..)
@app.route("/changeUserProfileAttribute", methods=["POST"])
def changeUserProfileAttribute():
    """ change user data according to what client says """
   
    getResult = request.get_json()
    newUserDescription = getResult["data"]
    jwt_token = getResult["jwtToken"]

    current_client = User(jwt_token)
    current_client.change_user_attribute(newUserDescription)

    return "Just a filler message, nothing to worry about"


# currently requested by the friends microservice.
@app.route('/userFriendsData', methods=["POST"])
def userData():
    # grab JWT token from friends microservice and return a username and friend_count so that the server can show the client how many friends they have
    getJson = request.get_json()

    jwt_token = getJson["jwt_token"]

    current_client = User(jwt_token)
    username = current_client.username
    userAttributes = current_client.get_user_attributes_from_db()
    friend_count = userAttributes[2]
    return jsonify({"username": username, "friend_count": friend_count})

if __name__ == '__main__': 
   app.run(port=5504)