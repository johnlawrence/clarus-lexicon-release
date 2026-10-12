from flask import Flask, request, g, render_template
from flask_babel import Babel, get_locale
from .routes import main
import sqlite3

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object('app.config.Config')

    # Define the locale selector
    def select_locale():
        lang = request.cookies.get('lang')
        if lang and lang in app.config['LANGUAGES']:
            return lang
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    # Initialize Babel (pass the selector function here)
    babel = Babel(app, locale_selector=select_locale)

    # Store selected language in g for templates
    @app.before_request
    def set_language():
        g.lang = select_locale()

    # Register blueprints
    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # --- Database connection helpers ---
    def get_db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row  # access rows like dicts
        return g.db

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # Make get_db available in other modules
    app.get_db = get_db

    # Make current locale available in templates
    @app.context_processor
    def inject_locale():
        return dict(current_locale=str(get_locale()))

    return app
