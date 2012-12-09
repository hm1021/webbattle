from google.appengine.ext import db

class Battle(db.Model):
	right = db.StringProperty(required = True)
	left = db.StringProperty(required = True)
	author = db.UserProperty(required = True)
	votes = db.IntegerProperty()
	comments = db.StringProperty(multiline = True)
	when = db.DateTimeProperty(auto_now_add = True)

class Comment(db.Model):
	comment = db.StringProperty(required = True,multiline = True)
	author = db.UserProperty(required = True)
	votes = db.IntegerProperty()
	side = db.StringProperty(required = True)
	when = db.DateTimeProperty(auto_now_add = True)

class UserVote(db.Model):
	author = db.UserProperty(required = True)
	vote = db.IntegerProperty(required = True)

class Post(db.Model):
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	when = db.DateTimeProperty(auto_now_add = True)
	author = db.UserProperty(required = True)