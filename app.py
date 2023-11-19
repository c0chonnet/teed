
from flask import Flask, render_template, Blueprint, g, redirect, request, current_app, abort, url_for
from flask_babel import Babel, _
import os
from config import Config
from sqlalchemy import create_engine, MetaData, Table, sql
import sshtunnel
from dotenv import load_dotenv
import json
import time
import folium
import folium.plugins
from PIL import Image
from cryptography.fernet import Fernet
import requests

app = Flask(__name__)
app.config.from_object(Config)
key = bytes(os.environ['FERNET'], encoding='utf8')
cipher_suite = Fernet(key)

########## DB ####################

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

############



####################### MULTILANG ############################

multilingual = Blueprint('multilingual', __name__, template_folder='templates', url_prefix='/<lang_code>')

# Babel
babel = Babel(app)

@multilingual.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang_code', g.lang_code)


@multilingual.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code = values.pop('lang_code')


@multilingual.before_request
def before_request():
    if g.lang_code not in app.config['LANGUAGES']:
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

@app.route('/end',methods=['GET'])
def end():
    visit=request.args.get('visit')
    if visit == 'none':
        iframe = 'none'

    else:

        with Tunneling() as t:
            with t.engine.connect() as connection:
                visitartworks = connection.execute(sql.text('''
                SELECT artworks.*, artists.name a_name, artists.ig
                FROM artworks JOIN visits_artworks ON visits_artworks.artwork_id = artworks.id 
                AND visits_artworks.visit_id = :visit
                JOIN artists ON artworks.artist_id = artists.id 
                ORDER BY random() limit 10;''').bindparams(visit=int(cipher_suite.decrypt(visit))))
        
        min_lat = 58.2
        min_lon = 26.5
        max_lat = 58.6
        max_lon = 26.8

        token = os.environ['MAPBOX']
        m = folium.Map(tiles= 'https://api.mapbox.com/styles/v1/c0chonnet/clhnpz6f701p801pr5dhp8tbh/tiles/256/{z}/{x}/{y}@2x?access_token='+token ,
                       position='absolute',
                       location=[58.3784716, 26.7229996],
                       zoom_start=13, max_zoom=16, min_zoom=12,
                       attr='© Mapbox 💗 #näitusteed',
                       control_scale=True,
                       min_lat=min_lat,
                       max_lat=max_lat,
                       min_lon=min_lon,
                       max_lon=max_lon,
                       prefer_canvas=True,
                       max_bounds=True
                       )
        points = []
        for a in visitartworks:
                if (float(a.lon), float(a.lat)) not in points:
                    points.append((float(a.lon), float(a.lat)))
                else:
                    continue

                icon_image = os.path.join(os.environ['UPLOAD_FOLDER'], 'pic', str(a.id) + '.png')
                im = Image.open(icon_image)
                w, h = im.size
                ic = folium.features.CustomIcon(icon_image, icon_size=(w * (80 / h), 80))
                mk = folium.Marker([a.lon, a.lat], icon=ic, popup=folium.Popup(f'''
                                               <b style="text-transform:uppercase;">{a.a_name}</b><br>
                                               <b>{a.name}. </b>{a.street} {a.building}<br>
                                               <a style="color:black;font-size:70%;" href="https://www.instagram.com/{a.ig}" target="_blank">@{a.ig}</a>
                                               '''))
                m.add_child(mk)

 #### ROUTING
        points = sorted(points, key=lambda l: [l[0], l[1]])
        st = ';'.join([str(a[1])+','+str(a[0]) for a in points])
        route_r = requests.get(f'''https://api.mapbox.com/directions/v5/mapbox/walking/{st}?alternatives=false&continue_straight=true&geometries=geojson&overview=simplified&steps=false&access_token={os.environ['NAVIGATION']}''')
        duration = round(route_r.json()['routes'][0]['duration']/3600)
        distance = round(route_r.json()['routes'][0]['distance']/1000,1)

        route = route_r.json()['routes'][0]['geometry']

##########
        style = {'color': '#dfd821','weight': 8}
        folium.GeoJson(route,  style_function=lambda x: style).add_to(m)
        m.get_root().width = "100%"
        m.get_root().height = "70vh"
        iframe = m.get_root()._repr_html_()

    return render_template('end.html',
                           iframe=iframe,
                           visit=visit,
                           duration=duration,
                           distance=distance)
@app.route('/visited', methods=['POST'])
def visited():
    ids=None

    if request.form.get('jsondata'):
        data = json.loads(request.form.get('jsondata'))
        ids = set(e['id'] for e in data)

    if 'end' in request.form and request.form['end'] == 'true':
        if ids is None or len(ids) == 1:
            return redirect(url_for('end', visit='none'))
        else:
            with Tunneling() as t:
                with t.engine.connect() as connection:
                    e_t = time.localtime()
                    end_time = time.strftime("%d.%m.%Y %H:%M:%S", e_t)
                    start_time = request.form['start']
                    query = sql.text('''INSERT INTO visits(start_time, end_time) 
                                VALUES (:start_time, :end_time) RETURNING id''')
                    query = query.bindparams(start_time=start_time, end_time=end_time)
                    result = connection.execute(query).fetchone()
                    visit = result.id
                    connection.commit()

                    for id in ids:
                        query = sql.text('''INSERT INTO visits_artworks (visit_id, artwork_id) 
                                                    VALUES (:visit, :artwork)''')
                        query = query.bindparams(visit=visit, artwork=id)
                        connection.execute(query)
                    connection.commit()
            return redirect(url_for('end', visit=cipher_suite.encrypt(bytes(str(visit), 'utf-8'))))
    return ''

@multilingual.route('/arscene')
def arscene():
    with open(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', '2' + '.txt'), "r", encoding='utf-8') as f:
        t2 = "\n".join(f.read().splitlines())
    with open(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', '3' + '.txt'), "r", encoding='utf-8') as f:
        t3 = "\n".join(f.read().splitlines())
    return render_template('arscene.html', t2=t2, t3=t3)


@app.route('/upload')
def upload():
      with Tunneling() as t:
        with t.engine.connect() as connection:
            artists = connection.execute(sql.text('SELECT * FROM artists;'))
            artworks = connection.execute(sql.text('''SELECT artworks.*, artists.name AS a_name
                                                   FROM artworks JOIN artists ON artists.id = artworks.artist_id;'''))

      return render_template('upload.html', artists=artists, artworks=artworks)


# Babel
babel = Babel(app)



def get_locale():
    if not g.get('lang_code', None):
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])

    return g.lang_code


babel.init_app(app, locale_selector=get_locale)
app.register_blueprint(multilingual)


@app.route('/')
def home():
    g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
    return redirect(url_for('multilingual.index'))
  


@app.route('/preview')
def preview( methods=['GET']):
    ids = request.args.get('id')
    ext = request.args.get('ext')

    text = None
    if ext == 'txt':
        with open(os.path.join(os.environ['UPLOAD_FOLDER'], 'assets', str(ids) + '.txt'), "r", encoding='utf-8') as f:
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

@app.route('/upload_artwork', methods=['POST','GET'])
def upload_artwork():

    target = request.files['target']
    if target.filename == '':
        istarget = False
    else:
        istarget = True


    with Tunneling() as t:
        with t.engine.connect() as connection:

            query = sql.text('''INSERT INTO artworks(artist_id, name, lon, lat, street, building, preview,year,price,materials) 
                     VALUES (:artist,:artwork_name,:lon,:lat,:street,:bld, :trg, :year, :price, :materials) RETURNING id''')
            query = query.bindparams(artist=request.form['artist'],
                                                       artwork_name=request.form['artwork-name'],
                                                       lon=request.form['lon'],
                                                       lat=request.form['lat'],
                                                       street=request.form['street'],
                                                       bld=request.form['bld'],
                                                       trg=istarget,
                                                       year=request.form['year'],
                                                       price=request.form['price'],
                                                       materials=request.form['materials'])
            result = connection.execute(query).fetchone()
            lastid=result.id

            query = sql.text('''INSERT INTO assets(artwork_id, type, credits) 
                                 VALUES (:a_id,:as_type, :credits)''')
            query = query.bindparams(a_id=lastid,
                                     as_type=request.form['assettype'],
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


    qr = url_for('preview', id=lastid,
                 ext=files['asset'].filename.rsplit('.', 1)[1].lower(),
                 _external=True)
    return render_template('ok.html', preview=istarget,
                           lastid=str(lastid),
                           qr=qr,
                           artworkname=request.form['artwork-name'])

