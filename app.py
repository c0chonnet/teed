from flask import Flask, render_template, Blueprint, g, redirect, request, current_app, abort, url_for
from flask_babel import Babel, _
from config import Config

####################### ROUTES ############################
multilingual = Blueprint('multilingual', __name__, template_folder='templates', url_prefix='/<lang_code>')


@multilingual.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)


@multilingual.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')


@multilingual.before_request
def before_request():
    if g.lang_code not in current_app.config['LANGUAGES']:
        adapter = app.url_map.bind('')
        try:
            endpoint, args = adapter.match('/en' + request.full_path.rstrip('/ ?'))
            return redirect(url_for(endpoint, **args), 301)
        except:
            abort(404)
    dfl = request.url_rule.defaults
    if 'lang_code' in dfl:
        if dfl['lang_code'] != request.full_path.split('/')[1]:
            abort(404)


@multilingual.route('/')
def index():
    return render_template('index.html', title=_('Home test'))


@multilingual.route('/visit')
def visit():
    return render_template('visit.html', title=_('Exhibition'))


@multilingual.route('/arscene')
def arscene():
    return render_template('arscene.html')


@multilingual.route('/upload')
def upload():
    return render_template('upload.html')


###########################################################


# App setup
app = Flask(__name__)
app.config.from_object(Config)

# Blueprint
app.register_blueprint(multilingual)

# Babel
babel = Babel(app)


def get_locale():
    if not g.get('lang_code', None):
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
    return g.lang_code


babel.init_app(app, locale_selector=get_locale)


@app.route('/')
def home():
    g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
    return redirect(url_for('multilingual.index'))
