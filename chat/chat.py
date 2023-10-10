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

app = Flask(__name__, template_folder="../templates", static_folder="../static")
socketio = SocketIO(app)
bcrypt = Bcrypt(app)

pepper = environ.get('SECRET_PEPPER')
private_key = environ.get('SECRET_KEY')
app.secret_key = environ.get('APP_SECRET_KEY')
conn = psycopg2.connect(environ.get('POSTGRES_URL'))

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
            return redirect('http://127.0.0.1:5502/login')
        except jwt.exceptions.InvalidTokenError:
            print("Sorry token invalid.")
            return redirect('http://127.0.0.1:5502/login')
        except Exception as e:
            print('err', e)
            print(traceback.format_exc())
            return redirect('http://127.0.0.1:5502/login')
        return func(*args, **kwargs)
    return inner_func


@app.route('/chat')
@check_for_token
def chat():
    return render_template('chat.html')

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


if __name__ == '__main__': 
   app.run(port=5500)