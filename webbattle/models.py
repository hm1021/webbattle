from google.appengine.ext import db

class Battle(db.Model):
	right = db.StringProperty(required = True)
	left = db.StringProperty(required = True)
	author = db.UserProperty(required = True)
	votes = db.IntegerProperty(default = 0)
	comments = db.StringProperty(multiline = True)
	when = db.DateTimeProperty(auto_now_add = True)
	subscribers = db.StringListProperty()
	tags = db.StringListProperty()
	expirationDate= db.DateTimeProperty()

class Comment(db.Model):
	comment = db.StringProperty(required = True,multiline = True)
	author = db.UserProperty(required = True)
	votes = db.IntegerProperty(default = 0)
	side = db.StringProperty(required = True)
	when = db.DateTimeProperty(required = True)
	blob = db.BlobProperty()

class Email(db.Model):
	email_address = db.EmailProperty(required = True)

class UserVote(db.Model):
	author = db.UserProperty(required = True)
	vote = db.IntegerProperty(default = 0)

class Post(db.Model):
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	when = db.DateTimeProperty(auto_now_add = True)
	author = db.UserProperty(required = True)