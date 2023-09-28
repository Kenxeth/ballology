# dependencies
from flask import Flask, render_template, request, make_response, redirect, url_for, flash
from flask_bcrypt import Bcrypt
# db dependencies
from pymongo import MongoClient
import psycopg2
# jwt token dependencies
import jwt
from functools import wraps

from flask_socketio import SocketIO, emit
import traceback

# env file dependencies
from dotenv import load_dotenv
from os import environ
load_dotenv()


# set up/boiler plate code
cluster = MongoClient(environ.get('MONGO_DB_URL'))
db = cluster["users"]
collection = db["user_credentials"]

app = Flask(__name__)
socketio = SocketIO(app)
bcrypt = Bcrypt(app)

# load env variables to use
pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')
app.secret_key = environ.get('APP_SECRET_KEY')

# SQL connection
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

# authorization
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
            print(traceback.format_exc())
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner_func


# chat feature
@socketio.on('connect')
def connect():
    print("client connected")

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    cursor = conn.cursor()
    sql_insert = ("""
        INSERT INTO messages (username, current_message)
        VALUES (%s, %s)
    """)

    # since message sender is always changing, we have to iterate through the message
    # and make both the message and the messagesender global variables so we can insert 
    # it inside of our DB

    for key,value in message.items():
        global username
        username = key
        global current_message 
        current_message = value
    
    new_message = (username, current_message)
    cursor.execute(sql_insert, new_message)
    conn.commit()

# chat messsage route
@app.route('/getChatMessages')
@check_for_token
def getChatMessages():
    cursor = conn.cursor()
    view_all_messages = ("""
        SELECT * from MESSAGES
    """)
    cursor.execute(view_all_messages)
    result = cursor.fetchall()
    print(result)
    conn.commit()
    return result

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
            flash("Sorry that username is already Taken. Please choose another one.")
            return redirect(url_for('register'))
        # insert username + encrypted password as a document
        collection.insert_one({'username': username, 'password': encrypted_password})
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return redirect(url_for('register'))
    return redirect(url_for('register'))

@app.route('/loginUser', methods=['POST'])
def loginUser():
    try:
        usernameGuess = request.form.get('username')
        print(type(pepper))
        print(type(request.form.get('password')))
        passwordGuess = request.form.get('password') + str(pepper)
        findCorrectUser = collection.find_one({'username': usernameGuess})
        if findCorrectUser is None:
            flash("Username not found.")
            return redirect(url_for('login'))
        correctPassword = findCorrectUser['password']
        if bcrypt.check_password_hash(correctPassword, passwordGuess):
            # password is correct in this case.
            encodedJWT = jwt.encode({"user": usernameGuess}, private_key, algorithm="HS256")
            response = make_response(redirect(url_for('chat')))
            response.set_cookie('JWT', encodedJWT, max_age=10000)
            response.set_cookie('username', usernameGuess)
        else:
            flash("Wrong password.")
            return redirect(url_for('login'))
    except jwt.ExpiredSignatureError:
        print("expired signature error")
        return redirect(url_for('login'))    
    except Exception as e:
        print("error: ", e)
        # prints out line error
        print(traceback.format_exc())
        return redirect(url_for('login'))
    return response

@app.route('/logout', methods=['POST'])
def logoutUser():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('JWT', '', expires=0)
    response.set_cookie("username", '', expires=0)
    return response



if __name__ == '__main__': 
   socketio.run(app)