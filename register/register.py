from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
# db dependencies
from pymongo import MongoClient
# jwt token dependencies
import psycopg2
import traceback

import pika
# env file dependencies
from dotenv import load_dotenv
from os import environ

load_dotenv()

# mongo 
cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]
# SQL
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

app = Flask(__name__, template_folder="../templates")
bcrypt = Bcrypt(app)

app.secret_key = environ.get('APP_SECRET_KEY')
pepper = environ.get('SECRET_PEPPER')


class RegisterUser:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.json_resp = None
        self.username_avaliability = None
        
    def check_username_avaliabilty(self):
        checkUserExists = collection.find_one({'username': self.username})
        
        if checkUserExists is not None:
            self.json_resp = jsonify({"message": "Sorry that username is already Taken. Please choose another one."})
            self.username_avaliability = False
        
        self.username_avaliability = True

    def insert_information_to_DBs(self):
        """
            Inserting credentials + user attributes into DB's. User attributes is needed for the profile page when the user is looked up.
        """
        
        if self.username_avaliability:
            # inserting credentials into mongoDB database
            collection.insert_one({'username': self.username, 'password': self.password})

            # inserting user attributes into SQL datbaase.
            cursor = conn.cursor()
            sql_insert = ("""
                INSERT INTO user_attributes (description, pfp, friend_count, username)
                VALUES (%s, %s, %s, %s)
                """)
            description = "Hi, I am a new user!"
            pfp = None
            friend_count = 0

            attributes = (description, pfp, friend_count, self.username)
            cursor.execute(sql_insert, attributes)
            conn.commit()

    def make_new_queue(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))    
        channel = connection.channel()
        channel.queue_declare(self.username)
        connection.close()


@app.route('/registerUser', methods=["POST"]) 
def registerUser():
    try:
        response = request.get_json(force=True)
        user = response["user"]
        username = user["username"]
        password = user["password"] + str(pepper)

        encrypted_password = bcrypt.generate_password_hash(password, 12)
        
        new_client = RegisterUser(username, encrypted_password)
        new_client.check_username_avaliabilty()

        if new_client.username_avaliability == False:
            return new_client.json_resp
        
        new_client.insert_information_to_DBs()
        new_client.make_new_queue()

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"message": "Sorry something went wrong. Please try again."})
    
    return jsonify({"message": "Success"})
    

if __name__ == '__main__': 
   app.run(port=5505)