import flask
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
# db dependencies
from pymongo import MongoClient
# jwt token dependencies
import jwt
from functools import wraps

# env file dependencies
from dotenv import load_dotenv
from os import environ

load_dotenv()

cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]


app = Flask(__name__, template_folder="../templates")
bcrypt = Bcrypt(app)

pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')
app.secret_key = environ.get('APP_SECRET_KEY')


class UserGuessedCredentials:
    """
        Checks if the user inputted the correct credentials in, in order to login into their account.

        username_guess (string): current guess for the username from the client
        password_guess (string): current guess for the password from the client
    """
    def __init__(self, username_guess, password_guess):
        self.username_guess = username_guess
        self.password_guess = password_guess
        self.json_resp = None # sends back JSON to the server

    def check_user(self):
        findCorrectUser = collection.find_one({"username": self.username_guess})
        
        if findCorrectUser is None: 
            self.json_resp = jsonify("Username not found.")
       
        correctPassword = findCorrectUser['password']
        
        if bcrypt.check_password_hash(correctPassword, self.password_guess):
            # password is correct in this case.
            encodedJWT = jwt.encode({"user": self.username_guess}, private_key, algorithm="HS256")
            self.json_resp = jsonify({"JWT": encodedJWT, "username": self.username_guess})
        else:
            self.json_resp = jsonify({"message": "Wrong password."})

        return self.json_resp
        
@app.route('/loginUser', methods=['POST'])
def loginUser():
    """
        Route to login the user
    """
    try:
        resp = request.get_json()
        
        user = resp["user"]
        username_guess = user["username"]
        password_guess = user["password"] + str(pepper)
        
        client_guess = UserGuessedCredentials(username_guess, password_guess)
        return client_guess.check_user()
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "expired signature error"}),404
    except Exception as e:
        return jsonify({"message": str(e)})
    

if __name__ == '__main__': 
   app.run(port=5502)