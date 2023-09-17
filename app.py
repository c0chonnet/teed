from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine, MetaData, Table, sql
import sshtunnel
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
tunnel = sshtunnel.SSHTunnelForwarder(
            (os.environ['PA_SSH'], 22),
            ssh_username=os.environ['PA_USER'],
            ssh_password=os.environ['PA_PWD'],
            remote_bind_address=(os.environ['RBA_HOST'], int(os.environ['RBA_PORT']))
            )

if os.environ['LOCAL'] == True:
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    engine1 = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
else:
    pass

class Tunneling:
    def __enter__(self):
        if os.environ['LOCAL'] == True:
            self.engine = engine1
        else:
            tunnel.start()
            self.engine = create_engine((os.environ['LOCALDB'] + str(tunnel.local_bind_port) + '/teed'), echo=True)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.environ['LOCAL'] == True:
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
    return render_template('upload.html', artists=artists)
@app.route('/upload_artwork', methods=['POST','GET'])
def upload_artwork():
    with Tunneling() as t:
        with t.engine.connect() as connection:
            query = sql.text('''INSERT INTO artworks(artist_id, name, lon, lat, street, building) 
                     VALUES (:artist,:artwork_name,:lon,:lat,:street,:bld) RETURNING id''')
            query = query.bindparams(artist=request.form['artist'],
                                                       artwork_name=request.form['artwork-name'],
                                                       lon=request.form['lon'],
                                                       lat=request.form['lat'],
                                                       street=request.form['street'],
                                                       bld=request.form['bld'])
            result = connection.execute(query).fetchone()
            lastid=result.id
            connection.commit()

            files = request.files

            if files['picture'].filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg']:
                ext = files['picture'].filename.rsplit('.', 1)[1].lower()
                files['picture'].save(os.path.join(os.environ['UPLOAD_FOLDER'], 'pic', str(lastid) + '.' + ext))

    return render_template('ok.html')

