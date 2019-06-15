from flask import Flask, render_template, request, redirect, session, flash, url_for
from mysqlconnection import connectToMySQL
app=Flask(__name__)
from flask_bcrypt import Bcrypt
bcrypt=Bcrypt(app)

import re
EMAIL_REGREX= re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app.secret_key="klsjdlka"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=["POST"])
def register_user():
    is_valid=True
    if not EMAIL_REGREX.match(request.form['email']):
        is_valid=False
        flash("Invalid email")
    db=connectToMySQL("first_flask_mysql")
    query="SELECT email from user_info where email = %(em)s"
    data= {
        "em": request.form['email']
    }
    em_count=db.query_db(query, data)
    if len(em_count) >1: #if comes back w more than one row, em already exist
        is_valid=False
        flash("Email already exist")
    if len(request.form['pw']) <8:
        is_valid=False
        flash("Need a longer password")
    if request.form['pw']!= request.form['cpw']:
        is_valid=False
        flash("Passwords must match")
    if len(request.form['first_name']) <2:
        is_valid=False
        flash("Need a longer name")
    if len(request.form['last_name']) <2:
        is_valid=False
        flash("Need a longer last name")
    if not is_valid:
        return redirect('/')
    else:
        pw_hash=bcrypt.generate_password_hash(request.form['pw'])
        print(pw_hash)
        db=connectToMySQL("first_flask_mysql")
        query="INSERT INTO user_info (first_name, last_name, email, pw) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s);"
        data ={
            "fn": request.form["first_name"],
            "ln": request.form["last_name"],
            "em": request.form["email"],
            "pw": pw_hash
        }
        user_id=db.query_db(query, data)
        session["user_id"]=user_id
        print("user id is:", user_id)
        return redirect('/dashboard')

@app.route('/login', methods=["POST"])
def login():
    db=connectToMySQL("first_flask_mysql") #connect to db
    query="SELECT id, email, pw from user_info WHERE email = %(em)s;" #query to see if em exist in db
    data = {
        "em": request.form['login_em'] 
    }
    log_info=db.query_db(query, data) #should give a {{[]}} with email and pw
    print(log_info)
    if len(log_info) <1: #if len of query <1, no email was in db
        flash('Invalid login')
        return redirect('/') #need to validate email
    log_pw=bcrypt.check_password_hash(log_info[0]['pw'], request.form['login_pw'])
    if not log_pw:    
        flash("Invalid login")
        return redirect('/')
    else:
        session['user_id']= log_info[0]['id']
        print(session['user_id'])
        
        return redirect ('/dashboard')
    
@app.route('/dashboard')
def dashboard():
    if  not "user_id" in session:
        flash("Invalid Login")
        return redirect('/')
    print("login info is:", session['user_id'])

    db=connectToMySQL("first_flask_mysql")
    query="SELECT first_name from user_info WHERE id = %(id)s;"
    data ={
        "id": session["user_id"]
    }
    user_info=db.query_db(query, data) #shows logged in user info
    print(user_info)


    db=connectToMySQL("first_flask_mysql")
    query="SELECT messages.id AS messageid, topic, content, messages.created_at, user_info.first_name AS sender, r.first_name AS receiver FROM user_info JOIN messages ON user_info.id=messages.sender_id JOIN user_info AS r ON messages.receip_id=r.id WHERE r.id= %(id)s ORDER BY messages.created_at DESC;" #shows messages from others to receip id
    data={
        "id": session["user_id"]
    }
    receip_info=db.query_db(query, data)


    sender_info=connectToMySQL("first_flask_mysql").query_db("SELECT id, first_name FROM user_info WHERE id != %(id)s", data={"id":session["user_id"]}) #shows all users not with the login id
    print (sender_info)
    return render_template("dashboard.html", rinfo=receip_info, info=user_info, sinfo=sender_info)

@app.route('/post', methods=["POST"])
def post():
    db=connectToMySQL("first_flask_mysql")
    query="INSERT INTO messages (topic, content, sender_id, receip_id) VALUES (%(topic)s,%(content)s,%(sid)s,%(rid)s);" #insert new message into table, getting sent to specific person
    data = {
        "topic": request.form["topic"],
        "content": request.form["content"],
        "sid": session["user_id"],
        "rid": request.form["receiver"]
    }
    db.query_db(query, data) #gives me message id
    return redirect("/dashboard")

@app.route('/delete', methods=["POST"])
def delete():
    db=connectToMySQL("first_flask_mysql")
    query="DELETE FROM messages WHERE messages.id=%(mi)s"
    data={
        "mi": request.form['message_id']
    }
    db.query_db(query, data)
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)