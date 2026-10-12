import os

class Config:
    LANGUAGES = ["en", "fi", "el", "cs", "pt"]
    BABEL_DEFAULT_LOCALE = "en"
    DATABASE = os.path.join(os.path.dirname(__file__), "..", "data", "lexicon.db")