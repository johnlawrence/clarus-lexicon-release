import unicodedata

from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, abort, g
from flask_babel import _

main = Blueprint('main', __name__)

# Reference alphabets for the /lexicon jump bar, in display order. Not used for
# sorting (that stays a plain SQL ORDER BY) - only for which letters are shown
# and which words fold into which letter's section. Letters listed here are
# treated as distinct (e.g. Finnish A/Ä, Czech C/C separately); anything else
# is folded to its base letter (stripping accents) if that base letter is
# listed, otherwise grouped under '#'.
ALPHABETS = {
    "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "pt": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "fi": "ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ",
    "cs": "AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYZÝŽ",
    "el": "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
}


def lexicon_group_key(word, alphabet):
    """First-letter grouping key for `word` against an ordered alphabet string.

    Tries an exact match first (so e.g. Finnish 'Ä' or Czech 'Č' land in their
    own section rather than folding into 'A'/'C'), then falls back to the
    accent-stripped base letter, then '#' for anything unrecognised.
    """
    if not word:
        return '#'
    ch = word[0].upper()
    if ch in alphabet:
        return ch
    base = ''.join(c for c in unicodedata.normalize('NFD', ch) if unicodedata.category(c) != 'Mn')
    if base in alphabet:
        return base
    return '#'

@main.route('/')
def index():
    # render the landing page with the search box
    return render_template('index.html')

@main.route('/set_language', methods=['POST'])
def set_language():
    """
    Set the language in a cookie (30 days) and redirect back.
    The language selector form POSTs here.
    """
    lang = request.form.get('language')
    next_url = request.referrer or url_for('main.index')
    resp = redirect(next_url)
    if lang and lang in current_app.config['LANGUAGES']:
        resp.set_cookie('lang', lang, max_age=30*24*3600, path='/')
    return resp

@main.route('/search_suggestions')
def search_suggestions():
    """Return up to 10 matching {id, word} pairs for the selected language."""
    query = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'en')
    if not query:
        return jsonify([])

    db = current_app.get_db()
    cursor = db.execute(
        """
        SELECT term_id, word
        FROM term_localizations
        WHERE language_code = ? AND word LIKE ?
        ORDER BY word LIMIT 10
        """,
        (lang, f"{query}%"),
    )
    suggestions = [{"id": row["term_id"], "word": row["word"]} for row in cursor.fetchall()]
    return jsonify(suggestions)

@main.route('/search')
def search():
    """Simple text-based search results for now."""
    query = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'en')
    db = current_app.get_db()
    cursor = db.execute(
        """
        SELECT t.id, tl.word, tl.definition
        FROM term_localizations tl
        JOIN terms t ON t.id = tl.term_id
        WHERE tl.language_code = ? AND tl.word LIKE ?
        ORDER BY tl.word
        """,
        (lang, f"%{query}%")
    )
    results = cursor.fetchall()

    # If the only result is an exact match, skip the list and go straight to the term.
    if len(results) == 1 and results[0]['word'].strip().lower() == query.lower():
        return redirect(url_for('main.term_entry', term_id=results[0]['id']))

    return render_template('search_results.html', query=query, results=results, lang=lang)


@main.route('/term/<int:term_id>')
@main.route('/term/<int:term_id>/<transl>')
def term_entry(term_id, transl=None):
    """Show a full entry for a term (all languages, English definition)."""
    db = current_app.get_db()
    
    # Get base term info (POS + frequency; definition is per-language, see localizations)
    term_cursor = db.execute(
        "SELECT id, pos, frequency FROM terms WHERE id = ?",
        (term_id,)
    )
    term = term_cursor.fetchone()
    if not term:
        abort(404)

    # Get all localizations for this term
    loc_cursor = db.execute(
        "SELECT language_code, word, category, definition, usage_example, left_collocates, right_collocates "
        "FROM term_localizations WHERE term_id = ?",
        (term_id,)
    )
    localizations = {row["language_code"]: dict(row) for row in loc_cursor.fetchall()}

    # Determine current language from g.lang or default
    current_lang = getattr(g, "lang", "en")

    if transl == None:
        transl = current_lang

    if transl not in localizations:
        abort(404)

    return render_template(
        "term_entry.html",
        term=term,
        localizations=localizations,
        current_lang=current_lang,
        trans_lang=transl,
        term_id=term_id
    )

@main.route('/about')
def about():
    """Show the About page in the current language.

    Content is full prose per language, not short UI strings, so it lives as
    HTML fragments in templates/about_content/<lang>.html rather than going
    through Flask-Babel's gettext (which is for short, exact-match strings).
    """
    lang = getattr(g, "lang", "en")

    if lang not in current_app.config['LANGUAGES']:
        abort(404)

    return render_template('about.html', lang=lang)

@main.route('/lexicon')
def lexicon():
    """Show all words in the selected language, grouped by starting letter."""
    # Determine current language from g.lang or default
    lang = getattr(g, "lang", "en")

    db = current_app.get_db()

    # Validate language
    if lang not in current_app.config['LANGUAGES']:
        abort(404)

    # Fetch term_id + word for that language
    rows = db.execute("""
        SELECT term_id, word
        FROM term_localizations
        WHERE language_code = ?
        ORDER BY LOWER(word) ASC
    """, (lang,)).fetchall()

    alphabet = ALPHABETS.get(lang, ALPHABETS['en'])

    # Build groups: letter -> [ { 'id': ..., 'word': ... }, ... ]
    groups = {}
    for row in rows:
        word = row['word']
        if not word:
            continue
        key = lexicon_group_key(word, alphabet)
        groups.setdefault(key, []).append({'id': row['term_id'], 'word': word})

    # Optionally sort words in each group (already ordered by SQL, but safe)
    for k in list(groups.keys()):
        groups[k] = sorted(groups[k], key=lambda x: x['word'].lower())

    total_count = sum(len(v) for v in groups.values())

    return render_template(
        'lexicon.html',
        lang=lang,
        groups=groups,
        alphabet=list(alphabet) + ['#'],
        total_count=total_count,
    )
