# dependencies
from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_bcrypt import Bcrypt
from os import environ
from dotenv import load_dotenv
from pymongo import MongoClient
from functools import wraps
import jwt
# set up/boiler plate code
cluster = MongoClient('mongodb+srv://todoAppUser:Kenneth2005@cluster0.idpy6zz.mongodb.net/?retryWrites=true&w=majority')
db = cluster["users"]
collection = db["user_credentials"]

app = Flask(__name__)
bcrypt = Bcrypt(app)
# load env variables to use
load_dotenv()
pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')

def check_for_token(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        try:
            JWT = request.cookies.get('JWT')
            if 'JWT' in request.cookies:
                decodedJWT = jwt.decode(JWT, private_key, algorithms=["HS256"])
                if decodedJWT == None:
                    raise jwt.exceptions.InvalidTokenError
            else:
                raise jwt.exceptions.DecodeError
        except jwt.exceptions.DecodeError:
            print("Sorry, not validated.")
            return redirect(url_for('login'))
        except jwt.exceptions.InvalidTokenError:
            print("Sorry token invalid.")
            return redirect(url_for('login'))
        except Exception as e:
            print('err', e)
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner_func

# basic routes
@app.route("/")
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return render_template('logout.html')

@app.route('/chat')
@check_for_token
def chat():
    return render_template('chat.html')
# POST routes

@app.route('/registerUser', methods=["POST"])
def registerUser():
    try:
        username = request.form.get('username')
        password = request.form.get('password') + str(pepper)
        # hash and add salt to the password + pepper
        # bcrypt returns a binary #
        encrypted_password = bcrypt.generate_password_hash(password, 12)
        # check if username exists
        checkUserExists = collection.find_one({'username': username})
        if checkUserExists is not None:
            raise Exception("Sorry username already Exists...")
        # insert username + encrypted password as a document
        collection.insert_one({'username': username, 'password': encrypted_password})
    except Exception as e:
        print(e)
        return redirect(url_for('register'))
    return redirect(url_for('register'))

@app.route('/loginUser', methods=['POST'])
def loginUser():
    try:
        usernameGuess = request.form.get('username')
        passwordGuess = request.form.get('password') + str(pepper)
        findCorrectUser = collection.find_one({'username': usernameGuess})
        if findCorrectUser is None:
            raise Exception("No Username Exists")
        correctPassword = findCorrectUser['password']
        if bcrypt.check_password_hash(correctPassword, passwordGuess):
            # password is correct in this case.
            encodedJWT = jwt.encode({"user": usernameGuess}, private_key, algorithm="HS256")
            response = make_response(redirect(url_for('chat')))
            response.set_cookie('JWT', encodedJWT, max_age=20)
        else:
            raise Exception("Sorry wrong password.")
    except jwt.ExpiredSignatureError:
        print("expired signature error")
        return redirect(url_for('login'))    
    except Exception as e:
        print("error: ", e)
        return redirect(url_for('login'))
    return response

@app.route('/logout', methods=['POST'])
def logoutUser():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('JWT', '', expires=0)
    return response

if __name__ == '__main__': 
   app.run()