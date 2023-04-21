from flask import Flask, render_template, request
import sqlite3 as sql
from random import randint

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'



def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


@app.route('/')
def index():
    return render_template('mainpage.html')


@app.route('/name', methods=['POST', 'GET'])
def name():
    error = None
    if request.method == 'POST':
        result = valid_name(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('input.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('input.html', error=error)


def valid_name(first_name, last_name):
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS users(pid INTEGER, firstname TEXT, lastname TEXT);')
    connection.execute('INSERT INTO users (pid, firstname, lastname) VALUES (?,?,?);', (random_with_N_digits(5), first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM users;')
    return cursor.fetchall()


if __name__ == "__main__":
    app.run()


