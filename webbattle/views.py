from webbattle import app
from models import Post, Battle, Comment
from flask import render_template, flash, redirect, url_for, request, jsonify
from flaskext import wtf
from flaskext.wtf import validators
from decorator import login_required
from google.appengine.api import users
from google.appengine.ext import db
from datetime import datetime

class PostForm(wtf.Form):
    title = wtf.TextField('Title', validators=[validators.Required()])
    content = wtf.TextAreaField('Content', validators=[validators.Required()])

class IndexForm(wtf.Form):
	left = wtf.TextField('Left', validators=[validators.Required()])
	right = wtf.TextField('Right', validators=[validators.Required()])

class CommentForm(wtf.Form):
	comment = wtf.TextAreaField('Comment', validators=[validators.Required()])

@app.route('/posts')
def list_posts():
	posts = Post.all()
	return render_template('list_posts.html', posts=posts)

@app.route('/posts/new',methods = ['GET','POST'])
@login_required
def new_post():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(title = form.title.data,
					content = form.content.data,
					author = users.get_current_user())
		post.put()
		flash('Post saved on database.')
		return redirect(url_for('list_posts'))
	return render_template('new_post.html', form=form)

def battle_key(left=None, right=None):
  	"""Constructs a Datastore key for a battle entity with left and right."""
  	return db.Key.from_path('Battle', left+right)

def comment_key(comment=None, author=None, when=None):
	"""constructs a Datastore key fr a comment entity with comment, author of the comment and the date of comment posted"""
	return db.Key.from_path('Comment', comment+author+when)

@app.route('/battle/<leftf>/<rightf>',methods = ['GET','POST'])
def left_right(leftf,rightf):
	left = CommentForm()
	right = CommentForm()
	left_comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =','left')
	right_comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =','right')
	time = datetime.now()
	if request.form.get('leftcomment'):
		leftComment = Comment(key_name = request.form.get('leftcomment')+users.get_current_user().nickname()+str(time),
							parent=battle_key(leftf,rightf),
							comment = request.form.get('leftcomment'),
							author = users.get_current_user(),
							side = "left",
							when = time)
		leftComment.put()
		return jsonify(lc=request.form.get('leftcomment'),author=users.get_current_user().nickname())
	elif request.form.get('rightcomment'):
		rightComment = Comment(key_name = request.form.get('rightcomment')+users.get_current_user().nickname()+str(time),
							parent=battle_key(leftf,rightf),
							comment = request.form.get('rightcomment'),
							author = users.get_current_user(),
							side = "right",
							when = time)
		rightComment.put()
		return jsonify(rc=request.form.get('rightcomment'),author=users.get_current_user().nickname())
	return render_template('battle.html',left=left,right=right,leftf=leftf,rightf=rightf,lc=left_comments,rc=right_comments)

@app.route('/battle/upvote/<leftf>/<rightf>',methods = ['GET','POST'])
def upvote_comment(leftf,rightf):
	comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =',request.form.get('side'))
	current_comment = comments.filter('comment =',request.form.get('comment')).filter('author =',users.User(request.form.get('author'))).filter('when =',datetime.strptime(request.form.get('when'),'%Y-%m-%d %H:%M:%S.%f')).get()
	current_comment.upvotes = current_comment.upvotes + 1
	current_comment.put()
	votes = current_comment.upvotes - current_comment.downvotes
	return jsonify(votes=votes)

@app.route('/battle/downvote/<leftf>/<rightf>',methods = ['GET','POST'])
def downvote_comment(leftf,rightf):
	comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =',request.form.get('side'))
	current_comment = comments.filter('comment =',request.form.get('comment')).filter('author =',users.User(request.form.get('author'))).filter('when =',datetime.strptime(request.form.get('when'),'%Y-%m-%d %H:%M:%S.%f')).get()
	current_comment.downvotes = current_comment.downvotes + 1
	current_comment.put()
	votes = current_comment.upvotes - current_comment.downvotes
	return jsonify(votes=votes)

@app.route('/',methods = ['GET','POST'])
@login_required
def index():
	form = IndexForm()
	if form.validate_on_submit():
		battle = Battle(key_name = form.left.data+form.right.data,
						left = form.left.data,
						right = form.right.data,
						author = users.get_current_user())
		battle.put()
		flash('The battle has been created.')
	battles = Battle.all()
	return render_template('new_battle.html', form=form, battles=battles)
