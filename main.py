from flask import Flask, render_template, request, redirect, url_for
from flask_bcrypt import Bcrypt
from os import environ
from pymongo import MongoClient
cluster = MongoClient('mongodb+srv://todoAppUser:Kenneth2005@cluster0.idpy6zz.mongodb.net/?retryWrites=true&w=majority')
db = cluster["users"]
collection = db["user_credentials"]

app = Flask(__name__)
bcrypt = Bcrypt(app)
# basic routes
@app.route("/")
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')
# POST routes
pepper = environ.get('SECRET_PEPPER')
@app.route('/registerUser', methods=["POST"])
def registerUser():
    try:
        username = request.form.get('username')
        password = request.form.get('password') + str(pepper)
        encrypted_password = bcrypt.generate_password_hash(password, 12)
        # check if username exists
        checkUserExists = collection.find_one({'username': username})
        if checkUserExists is not None:
            raise Exception("Sorry username already Exists...")
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
            print("Password is correct.")
        else:
            raise Exception("Sorry wrong password.")
    except Exception as e:
        print(e)
        return redirect(url_for('login'))
    return redirect(url_for('chat'))


if __name__ == '__main__': 
   app.run()