# -*- coding: utf-8 -*-
"""flask app run."""
from flask import Flask

from common import api_bp
import chat

app = Flask(__name__)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(debug=True)
