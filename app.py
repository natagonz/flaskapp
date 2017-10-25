from flask import Flask, render_template,flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message 
from itsdangerous import URLSafeTimedSerializer,SignatureExpired



app = Flask(__name__)
app.config.from_pyfile("config.cfg") #config for mail
mail = Mail(app)
s = URLSafeTimedSerializer("secret")

#mengatur mysql
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "myflaskapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
#init DB
mysql = MySQL(app)


#Articles = Articles()

app.debug = True


@app.route("/")
def main():
	return render_template("index.html")

@app.route("/about")
def about():
	return render_template("about.html")

@app.route("/articles")
def articles():
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0 :
		return render_template("articles.html",articles=articles)
	else:
		msg = "No article found"
		return render_template("articles.html",msg=msg)


	cur.close()



#membuat rute untuk artcle sesuai id,dengan parameter id dan passing id variable di template
@app.route("/article/<string:id>")
def article(id):
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM articles WHERE id =%s", [id])
	article = cur.fetchone()

	return render_template("article.html", article = article)



#mendefiskan form dengan WTF form validator

class RegisterForm(Form):
	name = StringField("Name", [validators.Length(min=1, max=100)] )
	username = StringField("Username", [validators.Length(min=1, max=100)])
	email = StringField("Email", [validators.Length(min=1, max=100)])
	password = PasswordField("Password",
		[
		validators.DataRequired(),
		validators.EqualTo("confirm", message="Password do not match")
		])
	confirm = PasswordField("Confirm password")

#membuat rute halaman register
@app.route("/register", methods=["GET","POST"])
def register():
	form = RegisterForm(request.form)
	if request.method == "POST" and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))#enkripsi oassword

		#membuat cursor
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO users(users_name, users_email, users_username, users_password) VALUES(%s,%s,%s,%s)",(name, email, username, password))

		#commint ke DB
		mysql.connection.commit()

		#menutup connection
		cur.close()

		#menambah flash mesaage
		flash("anda berhasil mendaftar", "success")
		return redirect(url_for("main"))

	return render_template("register.html", form=form)

#membuat user login route
@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form["username"]
		password_candidate = request.form["password"]

		#membuat cursor
		cur = mysql.connection.cursor()

		#mencocokan username saat request di form dengn username di mysql
		result = cur.execute("SELECT * FROM users WHERE users_username = %s" , [username])

		#mendapatkan data yang tersimpan
		if result > 0 :
			data = cur.fetchone()
			password = data["users_password"] #mengambil password yang tersimpan di database

			#membandingkan kecocokan password di request dengan database
			if sha256_crypt.verify(password_candidate,password) :
				#berhasil masuk username dan pssword cocok
				session["logged_in"] = True
				session["username"] = username

				flash("now you  are loggin", "success")
				return redirect(url_for("dashboard"))

			else :
				error = "Password Not Match"
				return render_template("login.html", error=error)

			cur.close()


		else :
			error = "Username not found"
			return render_template("login.html", error=error)

	return render_template("login.html")



#cek apakah user log in,bila tidak login tdk bisa melihat dashboard(flask decorator documentation)
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
        	return f(*args, **kwargs)
        else:
        	flash("Please Loggin","danger")
        	return redirect(url_for("main"))
    return wrap


#membuat route logout
@app.route("/logout")
@login_required
def logout():
	session.clear()
	flash("now you loggout","success")
	return redirect(url_for("main"))



#membuat rute  dashboard
@app.route("/dashboard/")
@login_required #memanggil fungsi login_required agar mengunci halaman dashboard hanya untuk loggin user
def dashboard() :
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0 :
		return render_template("dashboard.html",articles=articles)
	else:
		msg = "No article found"
		return render_template("dashboard.html",msg=msg)


	cur.close()





#membuat form article dengan WTF form
class ArticleForm(Form):
	title = StringField("Title", [validators.Length(min=1, max=50)] )
	body = TextAreaField("Body", [validators.Length(min=30)])


#menambah rute article
@app.route("/add_article",methods=["GET", "POST"])
@login_required #memanggil fungsi login_required agar mengunci halaman hanya untuk loggin user
def add_article() :
	form = ArticleForm(request.form)
	if request.method == "POST" and form.validate():
		title = form.title.data
		body = form.body.data

		cur = mysql.connection.cursor()
 		cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body,session["username"]))
 		mysql.connection.commit()
 		cur.close()

 		flash("Article created", "success")
 		return redirect(url_for("dashboard"))

 	return render_template("add_article.html", form=form)

 #menambah fungsi edit article
@app.route("/dashboard/edit_article/<string:id>",methods=["GET", "POST"])
@login_required #memanggil fungsi login_required agar mengunci halaman hanya untuk loggin user
def edit_article(id) :
	#agar form terisi langsung untuk di edit
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
	article = cur.fetchone()
	form = ArticleForm(request.form)

	form.title.data = article["title"]
	form.body.data = article["body"]

	if request.method == "POST" and form.validate():
		title = request.form["title"]
		body = request.form["body"]

		cur = mysql.connection.cursor()
 		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",[title,body,id])
 		mysql.connection.commit()
 		cur.close()

 		flash("Article Updated", "success")
 		return redirect(url_for("dashboard"))

 	return render_template("edit_article.html", form=form)

 #delete article
@app.route("/delete_article/<string:id>",methods=["POST"])
@login_required #memanggil fungsi login_required agar mengunci halaman hanya untuk loggin user
def delete_article(id) :
	#agar form terisi langsung untuk di edit
	cur = mysql.connection.cursor()
	result = cur.execute("DELETE FROM articles WHERE id=%s", [id])
	article = cur.fetchone()
	mysql.connection.commit()
 	cur.close()

 	flash("Article deleted", "success")
 	return redirect(url_for("dashboard"))










class ForgotPasswordForm(Form):
	password = PasswordField("Password",
		[
		validators.DataRequired(),
		validators.EqualTo("confirm", message="Password do not match")
		])
	confirm = PasswordField("Confirm password")

#forgot password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot():
	if request.method == "POST":
		email = request.form["email"]

		#membuat cursor
		cur = mysql.connection.cursor()

		#mencocokan username saat request di form dengn username di mysql
		result = cur.execute("SELECT * FROM users WHERE users_email = %s" , [email])

		#mendapatkan data yang tersimpan
		if result > 0 :
			token = s.dumps(email, salt="email-confirm")

			msg = Message("confirm email", sender="makinrame@gmail.com", recipients=[email])

			link = url_for("confirm", token=token, _external=True)

			msg.body = "your link is {}".format(link)
			mail.send(msg)
			return "You entered email is {} and the token is {}". format(email, token)
		else :
			return " Not match "

	return render_template("forgot.html")


	

@app.route("/confirm_password/<token>", methods=["GET","POST"])
def confirm(token):
	form = ForgotPasswordForm(request.form)
	try:
		email = s.loads(token, salt="email-confirm", max_age = 600)
	
		if request.method == "POST" and form.validate():
			password = sha256_crypt.encrypt(str(form.password.data))
			cur = mysql.connection.cursor()
 			cur.execute("UPDATE users SET users_password=%s WHERE users_email=%s",[password, email])
 			mysql.connection.commit()
 			cur.close()

 			flash("password Updated", "success")
 			return redirect(url_for("main"))
	except :
		return "expired"

	"""try:
		emails = s.loads(token, salt="email-confirm", max_age = 600)
	except SignatureExpired :
		return "Token expired"""

	

 	return render_template("password_reset.html", form=form)

































if __name__ == '__main__':
	app.secret_key ="secret123"
	app.run(host='0.0.0.0')
