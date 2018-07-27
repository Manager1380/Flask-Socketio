from flask import Flask, request, render_template, url_for, redirect, flash, session
from flask_socketio import SocketIO
import pymysql.cursors
from datetime import datetime
import json

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = "hello world please ino hads nazanid! :-)"
connection = pymysql.connect(host='127.0.0.1',
                             user='root',
                             password='funlife',
                             db='WhiteBoard',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

@socketio.on("connection")
def conn(a):
    print(a)

@app.route("/board"  , methods=['POST','GET'])
@socketio.on("message")
def board(message={"message":"","username":"Guest"}):
    message = json.dumps(message)
    new_message = json.loads(message)
    print("First Step Message Is Converted To Json Format")
    if session['username']:
        user = new_message['username']
        text = new_message['message']
        date = datetime.now().strftime("%Y-%m-%d")
        print("Username and Message and DateGive and in the variables", user, text, date)
        with connection.cursor() as cursor:
            sql  = "INSERT INTO `Messages` (`user`, `text`, `date`) VALUES (%s ,%s ,%s)"
            cursor.execute(sql,(user,text,date))
            connection.commit()
        # if method is get run this block
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `Messages`")
            data = cursor
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `onlineUsers`")
            onlineUsers = cursor
        return render_template("board.html",data=data,username=session['username'],onlineUsers=onlineUsers)
    else:
        flash("You Need To Login")
        return redirect(url_for("login"))

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@app.route("/login"  , methods=['POST','GET'])
def login():
    """
    1:    check if request method is POST
            get Username And Password
            Make a Connection To Database And Get The table `users`

            1-2:  Check Username and Password If Correct
                    Set Session Username
                    1-3 : Make a Connection To database And Check User login or not If User ghablan Do not Login
                            Insert Username And Userid To Table onlineUsers
                            and redirect to board route
                    1-3 :(if logined) echo you already logined
            1-2:(if !Correct)send flash (Wrong) and redirect to login route

    2:    return login template
    """
    x = 0
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        with connection.cursor() as cursor:
            sql = "SELECT * from `Users` WHERE username=(%s) AND password=(%s)"
            result = cursor.execute(sql, (username, password))
            if result:
                session['username'] = username
                cursor.execute("SELECT * FROM `onlineUsers` WHERE `username`=%s",(username))
                for i in cursor:
                    x = x+1
                if x == 0:
                    cursor.execute("SELECT * FROM Users WHERE username=%s", (username))
                    for i in cursor:
                        cursor.execute("INSERT INTO onlineUsers (`userid`,`username`) VALUES (%s, %s)", (i['id'],username))
                        connection.commit()
                    return redirect(url_for("board"))
                else:
                    return '''You have already login click below for logout<br>
                    <a href="http://localhost:5000/logout/">Logout</a>''' 
            else:
                flash("Username Or Password Wrong")
                return redirect(url_for("login"))
    else:
        return render_template("user/login.html")

@app.route("/register"  , methods=['POST','GET'])
def register():
    """
    1:  Check if request method Is POST
        Get Name, Username And Password
        1-2 :   Make a Connection To Database and Check Username is unique or not  if unique
                Make a Connection To Database And Insert The User into Users Table
                redirect User to Login Route
        1-2 :   if not unique
                send a flash ("username is already taken) & return register template
    2:  return register template  
    """
    if request.method == "POST":
        name     = request.form['name']
        username = request.form['username']
        password = request.form['password']
        with connection.cursor() as cursor:
            sql = "SELECT * FROM Users WHERE username = %s"
            result = cursor.execute(sql, (username))
            if result:
                flash("That username is already taken...")
                return render_template('user/register.html')
            else:
                sql = "INSERT INTO Users (name,username,password) VALUES (%s ,%s ,%s)"
                cursor.execute(sql,(name,username,password))
                connection.commit()
                return redirect(url_for("login"))
    else:
        return render_template("user/register.html")

@app.route("/logout"  , methods=['POST','GET'])
@app.route("/logout/"  , methods=['POST','GET'])
def logout():
    """
    1:  Check User Loginned? if loggined
        Make a Connection To Database and Delete Row Containt Username
        replace username wich None to session
        return redirect login route
    2:  if user !Loginned
        send flash (you did not login)
        return redirect login route

    """
    if session['username']:
        with connection.cursor() as cursor:
            sql = "DELETE FROM `onlineUsers` WHERE `username` = %s"
            cursor.execute(sql,(session['username']))
            connection.commit()
        session['username'] = None
        return redirect(url_for("login"))
    else:
        flash("you did not login")
        return redirect(url_for("login")) 

@app.route("/pv/<id>")
def PrivateChat(id):
    return "ok"

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@app.errorhandler(404)
def page_not_found(e):
    """
    If User Get a Wrong Route instead 404 default page reurn site_map template
    This Template Help User For Search Into Route And Select One Route 
    """
    links = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    return render_template("site_map.html",links=links),404



if __name__ == '__main__':
    app.debug = True
    socketio.run(app)

 
