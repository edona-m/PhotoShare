######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding




###################################################

from datetime import date
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/<string:s>", methods=['GET'])

@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', suppress=True)

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstName = request.form.get('firstName')
		lastName = request.form.get('lastName')
		gender = request.form.get('gender')
		birthDate = request.form.get('birthDate')
		homeTown = request.form.get('homeTown')
		
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstName, lastName, gender, birthDate, homeTown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, firstName, lastName, gender, birthDate, homeTown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
	self = getUserIdFromEmail(flask_login.current_user.id)
	friend = request.form.get('friendEmail')
	cursor = conn.cursor()
	friendsList = getFriendsList(self)
	if request.method == 'GET':
		photoList = getUsersPhotos(self)
		return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", profile=True, list=friendsList, photos=photoList, base64=base64)
	else: # POST
		searchTag = request.form.get('searchTag')
		
		if searchTag != None:
			s = str(request.form.get('searchTag')).lower().split(",")
			searchTag = [x.strip() for x in s]
			photoList = getUsersPhotosTag(self, searchTag)
			return render_template('hello.html', name=flask_login.current_user.id, message="Here's search results", profile=True, list=friendsList, photos=photoList, base64=base64)

		if friend != None:
			print(friend, searchTag)
			friend = getUserIdFromEmail(friend)
			addFriend(self, friend)
			friendsList = getFriendsList(self)
			return render_template('hello.html', name=flask_login.current_user.id, message="successfully added {0}!".format(friend), profile=True, list=friendsList)

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.photo_id, P.caption, A.name, U.email FROM Photos P, Albums A, Users U WHERE P.user_id = '{0}' AND P.user_id = U.user_id AND P.albums_id = A.albums_id ORDER BY A.name".format(uid))
	result = cursor.fetchall() 
	result = [list(tup) for tup in result] 
	for data in result:
		commentList = getComments(data[1])
		tagList = findTag(data[1])

		data.append(commentList)
		data.append(tagList)
	return result 

def getUsersPhotosTag(uid, searchTag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.photo_id, P.caption, A.name, U.email FROM Photos P, Albums A, Users U WHERE P.user_id = '{0}' AND P.user_id = U.user_id AND P.albums_id = A.albums_id ORDER BY A.name".format(uid))
	temp = cursor.fetchall() 
	temp = [list(tup) for tup in temp] 
	result = []
	for data in temp:
		commentList = getComments(data[1])
		tagList = findTag(data[1])
		
		contains = all(item in tagList for item in searchTag)
		
		if contains:
			data.append(commentList)
			data.append(tagList)
			
			result.append(data)
	return result 

#get all users in the database

# def friendsoffriends():
# 	#find users with mutual friends 
# 	uid = getUserIdFromEmail(flask_login.current_user.id)
# 	cursor = conn.cursor()
# 	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(uid))
# 	friends = cursor.fetchall()
# 	friends = [x for tup in friends for x in tup]
# 	mutualresult = []
# 	for friend in friends:
# 		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(friend))
# 		friendsOfFriends = cursor.fetchall()
# 		friendsOfFriends = [x for tup in friendsOfFriends for x in tup]
# 		for friendOfFriend in friendsOfFriends:
# 			if friendOfFriend not in friends and friendOfFriend != uid:
# 				cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendOfFriend))
# 				mutualresult.append(cursor.fetchone()[0])
	
# 	return mutualresult

#get photos that a user may also like 


	


	

	


	
#attpmpte to get top 3 photos with top 3 most popular tags, ran out of time 
def top3photos():
	
	uid = getUserIdFromEmail(flask_login.current_user.id)
	#tags= top3tags()
	cursor = conn.cursor()
	cursor.execute("SELECT P.photo_id FROM Photos P WHERE P.user_id = '{0}'".format(uid))
	photos = cursor.fetchall()
	photos = [x for tup in photos for x in tup]
	photoList = []
	for photo in photos:
		cursor.execute("SELECT T.name FROM Tags T, Tagged Tg WHERE Tg.photo_id = '{0}' AND T.tag_id = Tg.tag_id".format(photo))
		tagList = [x for tup in cursor.fetchall() for x in tup]
		#contains = all(item in tagList for item in tags)
		#if contains:
			#photoList.append(photo)
	return photoList





#find users with same hometown ? 
#offer reccomendations for users with mutual friends 

@app.route("/recommendations", methods=['GET', 'POST'])
@flask_login.login_required
def recommend():
	result = []
	uid = getUserIdFromEmail(flask_login.current_user.id) 

	friends= getFriendsList(uid) #get list of friends of curr user 
	for f in friends: 
		uid2= getUserIdFromEmail(f) #get users friend's id 
		fof= getFriendsList(uid2) #get list of friends of friends
		result.append(fof) #add to list of recommendations	
	#remove duplicates
	populartags= PopularUserTag(uid)
	#search for photos that have this tag

	#remove current user
	if flask_login.current_user.id in result:
		result.remove(flask_login.current_user.id)
	return render_template("recommendations.html", data=result[:3], tags=populartags)[:3]
#limit to 3 mutual recomendations 

def Contributes():
	cursor = conn.cursor()
	
	cursor.execute("SELECT U.email, (COUNT(C.user_id) + COUNT(P.user_id)) AS Contributes FROM Users U, Comments C, Photos P WHERE U.user_id = C.user_id AND U.user_id = P.user_id GROUP BY U.user_id ORDER BY Contributes DESC LIMIT 10")
	return cursor.fetchall()    
	
	

	
#find the tags associated with a photo    
def findTag(photoID):
	cursor = conn.cursor()
	cursor.execute("SELECT T.name FROM Tags T, Tagged Tg WHERE Tg.photo_id = '{0}' AND T.tag_id = Tg.tag_id".format(photoID))
	tagList = [x for tup in cursor.fetchall() for x in tup]
	return tagList

def addFriend(self, friend):
	
	#check if email is in the database 
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(self, friend))
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(friend, self))
	conn.commit()
	return True
	
	
	
#returns friend list 
def getFriendsList(self):
	cursor = conn.cursor()
	cursor.execute("SELECT U.email FROM photoshare.Friends F, photoshare.Users U WHERE F.user_id1 = {0} AND F.user_id2 = U.user_id;".format(self))
	friendsList = [element for tupl in cursor.fetchall() for element in tupl]

	return friendsList
#returns list of albums as tup (id, name)
def getUserAlbum(self):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id, name FROM Albums A WHERE user_id = '{0}'".format(self))
	alist = [(id,name) for (id, name) in cursor.fetchall()]
	print(alist)
	return alist

#returns album id given album name
def getUserAlbumName(self, name):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums A WHERE name = '{0}' AND user_id = '{1}'".format(name ,self))
	return cursor.fetchone()[0]


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		albumName = request.form.get('album')
		tags = str(request.form.get('tag')).lower().split(",") # make all tags lowercase, split by commas
		album = getUserAlbumName(uid, albumName)
		photo_data = imgfile.read()
		print(tags)

		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (caption, imgdata, albums_id, user_id) VALUES (%s, %s, %s, %s)''', (caption, photo_data, album, uid))
		conn.commit()

		for tag in tags:
			t = tag.strip()
			if newtag(tag.strip()):
				cursor.execute("INSERT INTO Tags (name) VALUES ('{0}')".format(t))
				conn.commit()
			
			cursor.execute("SELECT MAX(photo_id) FROM Photos")
			photoID = cursor.fetchone()[0]
			cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(t))
			tagID = cursor.fetchone()[0]
			cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES ('{0}', '{1}')".format(photoID, tagID))
			conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', albumList=getUserAlbum(uid))

   



@app.route('/upload/delete', methods=['GET', 'POST'])
@flask_login.login_required
def delete_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST': 
		photoID = request.form.get('photoID')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(photoID))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo {0} deleted!'.format(photoID), photos=getUsersPhotos(uid), base64=base64)
	else: 
		return render_template('upload.html', photos=getUsersPhotos(uid), base64=base64, delete=True)



def newtag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT T.name FROM Tags T WHERE T.name = '{0}'".format(tag))
	result = cursor.fetchall()
	if result: 
		return False
	else: 
		return True



# album creating
@app.route('/album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST': # album uploading
		today = date.today()
		# must have album name, owner id, date of creation requirement of database assignment 
		albumName = request.form.get('albumName')
		self = getUserIdFromEmail(flask_login.current_user.id)
		albumDate = today.strftime("%Y-%m-%d")
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (name, date, user_id) VALUES ('{0}', '{1}', '{2}')".format(albumName, albumDate, self))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album {0} created!'.format(albumName), album=getUserAlbumName(self, albumName))
	else: # GET, initial page
		return render_template('album.html', name=flask_login.current_user.id)

# album deletion
@app.route('/album/delete', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
	self = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST': # album deleting
		albumID = request.form.get('albumID')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(albumID))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album {0} deleted!'.format(albumID))
	else: # GET, initial page
		return render_template('album.html', delete=True, albumList=getUserAlbum(self))

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
	if request.method == 'GET':
		return render_template('dashboard.html', photos=getAllPhotos(), base64=base64, popularTags=getMostPopularTag())
	else: 
		commentPID = request.form.get('commentPhotoID')
		comment = request.form.get('comment')
		search = request.form.get('searchTag')
		likePID = request.form.get('likePhotoID')
		print(likePID)

		if search != None:
			search = str(search).lower().split(",")
			searchTag = [x.strip() for x in search]
			return render_template('dashboard.html', photos=getAllPhotosTags(searchTag), base64=base64, popularTags=getMostPopularTag())
		
		if commentPID != None:
			dt = date.today()
			creationDate = dt.strftime("%Y-%m-%d")
			uid = getUserIdFromEmail(flask_login.current_user.id)
			if commentCheck(uid, commentPID):
					return render_template('dashboard.html', message="Invalid Photo ID (cannot self-comment)", photos=getAllPhotos(), base64=base64, popularTags=getMostPopularTag())	
			else: 
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date) VALUES ('{0}', '{1}', '{2}', '{3}')".format(uid, commentPID, comment, creationDate))
				conn.commit()
				return render_template('dashboard.html', message="Commented on photo {0}!".format(commentPID), photos=getAllPhotos(), base64=base64, popularTags=getMostPopularTag())
	
			
		
		if likePID != None:
			print("you liked: ", likePID, "!")
			uid = getUserIdFromEmail(flask_login.current_user.id)
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(likePID, uid))
			conn.commit()
			numLikes = [[l, n] for (l, n) in countLikes(likePID)]

			return render_template('dashboard.html', message="Liked photo {0}!".format(likePID), photos=getAllPhotos(), base64=base64, numLikes=numLikes, popularTags=getMostPopularTag())

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.photo_id, P.caption, A.name, U.email FROM Photos P, Albums A, Users U WHERE P.user_id = U.user_id AND P.albums_id = A.albums_id ORDER BY A.name")
	result = cursor.fetchall() 
	result = [list(tup) for tup in result] 
	for data in result:
		tlist = findTag(data[1])
		clist = getComments(data[1])
	
		data.append(clist)
		data.append(tlist)
	return result 

def getHometown():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor=conn.cursor()
	cursor.execute("SELECT U.hometown FROM WHERE user_id = '{0}'".format(uid))
	result = cursor.fetchall()
	return result
		

def getAllPhotosTags(searchTag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.photo_id, P.caption, A.name, U.email FROM Photos P, Albums A, Users U WHERE P.user_id = U.user_id AND P.albums_id = A.albums_id ORDER BY A.name")
	temp = cursor.fetchall()
	temp = [list(tup) for tup in temp] 
	result = []
	for data in temp:
		cList = getComments(data[1])
		
		tList = findTag(data[1])

		contains = all(item in tList for item in searchTag)
		if contains:
			data.append(cList)
			data.append(tList)

			result.append(data)
	return result 



def getMostPopularTag():
	cursor = conn.cursor()
	cursor.execute("SELECT T.tag_id, COUNT(*) FROM Tagged T GROUP BY T.tag_id HAVING COUNT(*) = (SELECT MAX(nor) FROM (SELECT T.tag_id, COUNT(*) as nor FROM Tagged T GROUP BY T.Tag_id) as X)")
	result = [list(tup) for tup in cursor.fetchall()]
	for tag in result:
		cursor.execute("SELECT name FROM Tags T WHERE tag_id = '{0}'".format(tag[0]))
		tag.append(cursor.fetchone()[0]) 
	return(result)


def PopularUserTag(uid):
	cursor=conn.cursor()
	cursor.execute("SELECT T.tag_id, COUNT(*) FROM Tagged T, Photos P WHERE T.photo_id = P.photo_id AND P.user_id = '{0}' GROUP BY T.tag_id HAVING COUNT(*) = (SELECT MAX(nor) FROM (SELECT T.tag_id, COUNT(*) as nor FROM Tagged T, Photos P WHERE T.photo_id = P.photo_id AND P.user_id = '{0}' GROUP BY T.Tag_id) as X)".format(uid))
	result = [list(tup) for tup in cursor.fetchall()]
	for tag in result:
		cursor.execute("SELECT name FROM Tags T WHERE tag_id = '{0}'".format(tag[0]))
		tag.append(cursor.fetchone()[0])
	return(result)


def commentCheck(self, photoID):
	cursor = conn.cursor()
	cursor.execute("SELECT P.user_id FROM Photos P WHERE P.photo_id = {0}".format(photoID))
	result = cursor.fetchone()[0]
	
	if self == result:
		return True
	else:
		return False 
def getComments(photoID):
	cursor = conn.cursor()
	cursor.execute("SELECT C.text, C.date, U.email FROM Comments C, Users U WHERE C.user_id = U.user_id AND C.photo_id = {0}".format(photoID))
	result = [list(tup) for tup in cursor.fetchall()]
	return result

def countLikes(photoID):
	cursor = conn.cursor()
	cursor.execute("SELECT L.photo_id, COUNT(L.user_id) FROM Likes L GROUP BY photo_id")
	return cursor.fetchall()

#default page
@app.route("/", methods=['GET'])
def hello():
	contributionList = [[email, score] for (email, score) in Contributes()]
	return render_template('hello.html', message='Welecome to Photoshare', contributionList=contributionList)



if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
