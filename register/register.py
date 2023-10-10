from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
# db dependencies
from pymongo import MongoClient
# jwt token dependencies
import psycopg2
import traceback

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



def insert_user_attributes_into_db(username):
    cursor = conn.cursor()
    sql_insert = ("""
        INSERT INTO user_attributes (description, pfp, friend_count, username)
        VALUES (%s, %s, %s, %s)
        """)
    description = "Hi, I am a new user!"
    pfp = None
    friend_count = 0

    attributes = (description, pfp, friend_count, username)
    cursor.execute(sql_insert, attributes)
    conn.commit()


@app.route('/registerUser', methods=["POST"]) 
def registerUser():
    try:
        response = request.get_json(force=True)
        user = response["user"]
        username = user["username"]
        password = user["password"] + str(pepper)
        encrypted_password = bcrypt.generate_password_hash(password, 12)
        checkUserExists = collection.find_one({'username': username})
        if checkUserExists is not None:
            return jsonify({"message": "Sorry that username is already Taken. Please choose another one."})
        collection.insert_one({'username': username, 'password': encrypted_password})
        insert_user_attributes_into_db(username)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"message": "Sorry something went wrong. Please try again."})
    
    return jsonify({"message": "Success"})
    



if __name__ == '__main__': 
   app.run(port=5505)