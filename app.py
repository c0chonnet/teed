from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine, MetaData, Table, sql
import sshtunnel
from dotenv import load_dotenv

app = Flask(__name__)

if os.environ['LOCAL'] == 'True':
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    engine1 = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
else:
    load_dotenv()
    sshtunnel.SSH_TIMEOUT = 5.0
    sshtunnel.TUNNEL_TIMEOUT = 5.0
    tunnel = sshtunnel.SSHTunnelForwarder(
        (os.environ['PA_SSH'], 22),
        ssh_username=os.environ['PA_USER'],
        ssh_password=os.environ['PA_PWD'],
        remote_bind_address=(os.environ['RBA_HOST'], int(os.environ['RBA_PORT']))
    )

class Tunneling:
    def __enter__(self):
        if os.environ['LOCAL'] == 'True':
            self.engine = engine1
        else:
            tunnel.start()
            self.engine = create_engine((os.environ['LOCALDB'] + str(tunnel.local_bind_port) + '/teed'), echo=True)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.environ['LOCAL'] == 'True':
            pass
        else:
            tunnel.close()

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
    with Tunneling() as t:
        with t.engine.connect() as connection:
            artists = connection.execute(sql.text('SELECT * FROM artists;'))
            artworks = connection.execute(sql.text('''SELECT artworks.id, artworks.name, artists.name AS aname
                                                   FROM artworks JOIN artists ON artists.id = artworks.artist_id;'''))
    return render_template('upload.html', artists=artists, artworks=artworks)


@app.route('/preview')
def preview( methods=['GET']):
    ids = request.args.get('id')
    ext = request.args.get('ext')

    text = None
    if ext == 'txt':
        with open(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', str(ids) + '.txt'), "r") as f:
            text = "\n".join(f.read().splitlines())

    sound = None
    if os.path.exists(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', str(ids) + '.mp3')):
        sound = os.path.join(os.environ['UPLOAD_FOLDER'],
                                              'assets', str(ids) + '.mp3')

    return render_template('preview.html', id=ids, ext=ext, text=text, sound=sound)

@app.route('/delete_only_admin', methods=['POST','GET'])
def delete_only_admin():
    with Tunneling() as t:
        with t.engine.connect() as connection:
            artists = connection.execute(sql.text('SELECT * FROM artists;'))
            artworks = connection.execute(sql.text('''SELECT artworks.id, artworks.name, artists.name AS aname
                                                   FROM artworks JOIN artists ON artists.id = artworks.artist_id;'''))
    return render_template('delete.html', artworks=artworks)

@app.route('/delete_artwork', methods=['POST','GET'])
def delete_artwork():
    with Tunneling() as t:
        with t.engine.connect() as connection:
            query = sql.text('DELETE FROM assets WHERE artwork_id = :id;')
            query = query.bindparams(id=request.form['deleteartwork'])
            connection.execute(query)
            query = sql.text('DELETE FROM artworks WHERE id = :id;')
            query = query.bindparams(id=request.form['deleteartwork'])
            connection.execute(query)
            connection.commit()

    for root, dirs, files in os.walk(os.environ['UPLOAD_FOLDER']):
        for file in files:
            if file.rsplit('.', 1)[0].lower() == str(request.form['deleteartwork']):
                os.remove(os.path.join(root, file))
    return render_template('ok.html')


@app.route('/request_change', methods=['POST','GET'])
def request_change():
    with Tunneling() as t:
        with t.engine.connect() as connection:
            query = sql.text('UPDATE assets SET request = :crequest WHERE artwork_id = :id;')
            query = query.bindparams(id=request.form['changeartwork'],
                                     crequest=request.form['requestchange'])
            connection.execute(query)
            connection.commit()
    return render_template('ok.html')


@app.route('/upload_artwork', methods=['POST','GET'])
def upload_artwork():

    target = request.files['target']
    if target.filename == '':
        istarget = False
    else:
        istarget = True

    sound = request.files['sound']
    if sound.filename == '':
        issound = False
    else:
        issound = True

    with Tunneling() as t:
        with t.engine.connect() as connection:

            query = sql.text('''INSERT INTO artworks(artist_id, name, lon, lat, street, building, preview) 
                     VALUES (:artist,:artwork_name,:lon,:lat,:street,:bld, :trg) RETURNING id''')
            query = query.bindparams(artist=request.form['artist'],
                                                       artwork_name=request.form['artwork-name'],
                                                       lon=request.form['lon'],
                                                       lat=request.form['lat'],
                                                       street=request.form['street'],
                                                       bld=request.form['bld'],
                                                       trg=istarget)
            result = connection.execute(query).fetchone()
            lastid=result.id

            query = sql.text('''INSERT INTO assets(artwork_id, type, sound, credits) 
                                 VALUES (:a_id,:as_type,:sound,:credits)''')
            query = query.bindparams(a_id=lastid,
                                     as_type=request.form['assettype'],
                                     sound=issound,
                                     credits=request.form['credits'])
            connection.execute(query)
            connection.commit()

        files = request.files

        if files['picture'].filename.rsplit('.', 1)[1].lower() == 'jpg':
            files['picture'].save(os.path.join(os.environ['UPLOAD_FOLDER'], 'pic', str(lastid) + '.jpg'))

        if files['asset'].filename.rsplit('.', 1)[1].lower() in ['glb', 'gif', 'png', 'txt']:
            ext = files['asset'].filename.rsplit('.', 1)[1].lower()
            files['asset'].save(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', str(lastid) + '.' + ext))

        if istarget == True:
            files['target'].save(os.path.join(os.environ['UPLOAD_FOLDER'], str(lastid) + '.mind'))

        if issound == True:
            files['sound'].save(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', str(lastid) + '.mp3'))

    qr = url_for('preview', id=lastid,
                 ext=files['asset'].filename.rsplit('.', 1)[1].lower(),
                 _external=True)
    return render_template('ok.html', preview=istarget,
                           lastid=str(lastid),
                           qr=qr,
                           artworkname=request.form['artwork-name'])

