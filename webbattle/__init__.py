from flask import Flask
import settings

app = Flask('webbattle')
app.config.from_object('webbattle.settings')

import views
