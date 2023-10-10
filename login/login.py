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

@app.route('/loginUser', methods=['POST'])
def loginUser():
    try:
        resp = request.get_json()
        print(resp)
        user = resp["user"]
        usernameGuess = user["username"]
        passwordGuess = user["password"] + str(pepper)

        findCorrectUser = collection.find_one({'username': usernameGuess})
        if findCorrectUser is None:
            return jsonify("Username not found.")
        correctPassword = findCorrectUser['password']
        if bcrypt.check_password_hash(correctPassword, passwordGuess):
            # password is correct in this case.
            encodedJWT = jwt.encode({"user": usernameGuess}, private_key, algorithm="HS256")
            return jsonify({"JWT": encodedJWT, "username": usernameGuess})
        else:
            return jsonify({"message": "Wrong password."})
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "expired signature error"}),404
    except Exception as e:
        return jsonify({"message": str(e)})
    

    
if __name__ == '__main__': 
   app.run(port=5502)