from google.appengine.ext import db

class Battle(db.Model):
	right = db.StringProperty(required = True)
	left = db.StringProperty(required = True)
	author = db.UserProperty(required = True)
	votes = db.IntegerProperty(default = 0)
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
	blob_key = db.StringProperty() 
	image_url = db.StringProperty(default = "None") 

class UserVote(db.Model):
	author = db.UserProperty(required = True)
	vote = db.IntegerProperty(default = 0)