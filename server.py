from flask import Flask, render_template, request, redirect, session, flash, url_for
from mysqlconnection import connectToMySQL
app=Flask(__name__)
from flask_bcrypt import Bcrypt
bcrypt=Bcrypt(app)

import re
EMAIL_REGREX= re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app.secret_key="klsjdlka"
USER_KEY='user_id'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=["POST"])
def register():
    #validating user info, check if length long enough
    is_valid=True
    #check if email is in use
    if not EMAIL_REGREX.match(request.form['email']):
        is_valid=False
        flash("Require valid email address")
        return redirect('/')
    #check if email is in valid format and matches with confirm pw
    if request.form['pw'] != request.form['cpw']:
        is_valid= False
        flash("Passwords must match")
        return redirect('/')
    if len(request.form['pw'])<8:
        is_valid= False
        flash ("Password needs to be 8 or more characters")
    db=connectToMySQL("first_flask_mysql")
    query="SELECT email from login_info;"
    print("emails:", query)
    used_email=db.query_db(query)
    for user in used_email:
        if user['email']==request.form['email']:
            is_valid= False
            flash("Email already exist. Try another")
    if len(request.form['first_name']) <2:
        is_valid=False
        flash("Require first name longer than 2 char")
    if len(request.form['last_name']) <2:
        is_valid=False
        flash("Require  last name longer than 2 char")
    if not is_valid:
        return redirect ('/')
    else:   
        pw_hash= bcrypt.generate_password_hash(request.form['pw'])
        db=connectToMySQL("first_flask_mysql")
        query="INSERT INTO login_info (first_name, last_name, email, pw) VALUES (%(fn)s,%(ln)s,%(em)s,%(pw)s);"
        data = {
            "fn" : request.form["first_name"],
            "ln" : request.form["last_name"],
            "em" : request.form["email"],
            "pw" : pw_hash
        }
        user_id=db.query_db(query, data)
        return redirect(url_for('user_dash',user_id = user_id))
@app.route('/userdash/<user_id>')
def user_dash(user_id):
    print(user_id)
    db=connectToMySQL("first_flask_mysql")
    query="SELECT * FROM login_info WHERE id= %(id)s"
    data = {
        "id": user_id
    }
    user_info=db.query_db(query, data)
    print(user_info)
    return render_template('dashboard.html', user_info=user_info)

@app.route('/login', methods=["POST"])
def login():
    db=connectToMySQL("first_flask_mysql")
    query="SELECT id, pw from login_info WHERE email=%(login_em)s;"
    data = {
        "login_em": request.form['login_em']
    }
    login_info=db.query_db(query, data)
    if not EMAIL_REGREX.match(request.form['login_em']):
        flash("Invalid login") #need to print validation on html
        return redirect('/')
    pw_hash= bcrypt.check_password_hash(login_info[0]['pw'], request.form['login_pw'])
    if not pw_hash:
        flash("Invalid Login")
        return redirect('/')
    else:
        print("success!!!!", "*"*50)
        session['user_id']=login_info[0]['id']
        user_id=session['user_id']
    return redirect("/userdash/" + str(user_id))

@app.route('/post', methods=['POST'])
def post():
    db=connectToMySQL("first_flask_mysql")
    query = "INSERT INTO messages (topic, content, sender_id) VALUES (%(topic)s,%(content)s, %(sender_id)s);"
    data={
        "topic": request.form['topic'],
        "content": request.form['content'],
        "sender_id": session['user_id']
    }
    post_id=db.query_db(query, data)
    print ("post_id:", post_id)
    return redirect ('/getpost') 
     #(url_for('user_dash',user_id=session["user_id"])) #dont want to have it queried in user_dash, just want to go back to page

@app.route('/getpost')
def getpost():
    db=connectToMySQL("first_flask_mysql")
    query="SELECT login_info.id, login_info.first_name, login_info.last_name, \
        messages.topic, messages.content, messages.sender_id, messages.created_at \
        FROM login_info \
            JOIN messages ON messages.sender_id = login_info.id WHERE login_info.id = %(login_id)s \
                ORDER BY messages.created_at DESC;"
    data = {
        "login_id": session['user_id']
    }
    sender_info = db.query_db(query, data)
    print("*"*80)
    print(sender_info)
    
    db=connectToMySQL("first_flask_mysql")
    query="SELECT * FROM login_info WHERE id= %(id)s"
    data = {
        "id": session['user_id']
    }
    user_info=db.query_db(query, data)
    return render_template("dashboard.html", contents=sender_info, user_info=user_info) #need to print sender_id, name, topic, content out onto html

@app.route('/logout')
def log_out():
    session.clear()
    return redirect('/')
if __name__=="__main__":
    app.run(debug=True)

# @app.route('/example')
# def wall():
#     return render_template("wall.html")