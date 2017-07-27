from flask import Flask, render_template,flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
#mengatur mysql
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "myflaskapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
#init DB
mysql = MySQL(app)


Articles = Articles()

app.debug = True


@app.route("/")
def main():
	return render_template("index.html")

@app.route("/about")
def about():
	return render_template("about.html")

@app.route("/articles")
def articles():
	return render_template("articles.html", articles = Articles)
#membuat rute halaman artikel,semua artikel yang ada dari data.py dan passing variable articles di articles.html


@app.route("/article/<string:id>")
def article(id):
	return render_template("article.html", id = id)
#membuat rute untuk artcle sesuai id,dengan parameter id dan passing id variable di template



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


#membuat route logout
@app.route("/logout")
def logout():
	session.clear()
	flash("now you loggout","success")
	return redirect(url_for("main"))

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





#membuat rute  dashboard
@app.route("/dashboard")
@login_required #memanggil fungsi login_required agar mengunci halaman dashboard hanya untuk loggin user
def dashboard() :
	return render_template("dashboard.html")










if __name__ == '__main__':
	app.secret_key ="secret123"
	app.run()