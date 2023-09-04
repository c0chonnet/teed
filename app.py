from flask import Flask, render_template

app = Flask(__name__)\

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visit')
def visit():
    return render_template('visit.html')

@app.route('/arscene')
def arscene():
    return render_template('arscene.html')

@app.route('/upload')
def upload():
    return render_template('upload.html', h1='Artwork upload',
                           title='TEED | Artwork upload', upload=True)