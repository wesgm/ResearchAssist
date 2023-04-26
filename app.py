from flask import Flask, jsonify, request, render_template, redirect, url_for
import json
import pickle
import sqlite3
from classes import User, Conversation
from llama_index import GPTSimpleVectorIndex
import os
from werkzeug.utils import secure_filename


CONNECTION = sqlite3.connect('researchassist.db')
CURSOR = CONNECTION.cursor()
CURSOR.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, data BLOB)')
CONNECTION.commit()

class InsertedExistingUserException(Exception):
    pass

class UserNotInDatabaseException(Exception):
    pass

class ConversationNotFoundException(Exception):
    pass

app = Flask(__name__)

def putUser(user: User):
    userData = pickle.dumps(user)
    try:
        CURSOR.execute('INSERT INTO users (id, data) VALUES (?, ?)', (user.id, userData))
        CONNECTION.commit()
    except sqlite3.IntegrityError:
        raise InsertedExistingUserException

def updateUser(user: User):
    userData = pickle.dumps(user)
    CURSOR.execute('UPDATE users SET data=? WHERE id=?', (userData, user.id))
    CONNECTION.commit()
    if(CURSOR.rowcount == 0):
        raise UserNotInDatabaseException

def getUser(id: int) -> User:
    CURSOR.execute('SELECT data FROM users WHERE id=?', (id,))
    userData = CURSOR.fetchone()[0]
    if userData is None:
        raise UserNotInDatabaseException
    return pickle.loads(userData)


@app.route('/upload', methods=['POST'])
def handleFileUpload(request: request):
    id = request.cookies.get('user_id')
    try:
        user = getUser(id)
    except UserNotInDatabaseException:
        user = User(id)
        putUser(user)
    index = user.constructIndex(request)
    updateUser(user)
    # generate redirect to upload-complete
    return redirect('/upload-complete', code=302)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload-complete')
def uploadComplete():
    return render_template("upload-complete.html")

def ask(request: request) -> str:
    id = request.cookies.get('user_id')
    user = getUser(id) #watch out for UserNotInDatabaseException when calling ask!
    conversation = user.conversations.get(request.SOMETHING)
    if conversation is None:
        raise ConversationNotFoundException
    userPrompt = request.SOMETHING_ELSE
    response = ""

def clearDatabase():
    CURSOR.execute('DELETE FROM users')
    CONNECTION.commit()

def mainFn():
    user = User(5000)
    user.conversations['test'] = Conversation('test', None, None, True)
    try:
        putUser(user)
    except InsertedExistingUserException:
        print('User already exists')
    user = getUser(5000)
    print(user.conversations['test'].subject)

if __name__ == '__main__':
    DEBUG=False
    if DEBUG:
        clearDatabase()
        mainFn()
    app.run()



