from setup import setup

setup()
import os
from functools import wraps
import tempfile
from datetime import timedelta

import logs
from flask import Flask, redirect, render_template, request, make_response, jsonify, url_for
from paste.translogger import TransLogger
from waitress import serve
from models import User

from api import ApiPostgREST, ApiPasswordless

logger = logs.get_logger('Web', token=os.getenv('LOGTAIL_WEB'))
logger.info('Starting Web')

cert_env = os.getenv('CERT')
if cert_env:
    cert_f = tempfile.NamedTemporaryFile(delete=False)
    cert_f.write(bytes(cert_env, 'utf-8'))
    cert_f.close()
    cert_env = cert_f.name

key_env = os.getenv('CERT_KEY')
if key_env:
    key_f = tempfile.NamedTemporaryFile(delete=False)
    key_f.write(bytes(key_env, 'utf-8'))
    key_f.close()
    key_env = key_f.name

api = ApiPostgREST(url=os.getenv('URL'), cf_client_id=os.getenv('CF_CLIENT_ID'),
                   cf_client_secret=os.getenv('CF_CLIENT_SECRET'), cert_f=cert_env, key_f=key_env,
                   api_key=os.getenv('API_KEY'), api_key_name=os.getenv('API_KEY_NAME'))

api_pwl = ApiPasswordless(url=os.getenv('PWL_URL'), api_secret_key=os.getenv('PWL_PRIVATE_KEY'))

app = Flask(__name__, template_folder='templates', static_folder='static')
SESSION_NAME = "SessionID"

ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b']


def logout_fun(sessionid):
    api.delete_session(sessionid)
    resp = make_response(redirect('/'))
    resp.delete_cookie(SESSION_NAME)
    return resp


def get_user(sessionid) -> User | None:
    return api.get_user_by_sessionid(sessionid)


def check_logged():
    sessionid = request.cookies.get(SESSION_NAME)
    if sessionid is not None:
        return get_user(sessionid)


def login_req(role=0, change_pw=True):
    def decorate(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            user = check_logged()
            if user is not None:
                logger.info(f'{fun.__name__}:{user}')
                api.session_used(user.sessionid)
                if change_pw and user.change_pw:
                    return redirect(url_for('profile'))
                if user.role >= role:
                    return fun(user, *args, **kwargs)

                return logout_fun(user.sessionid)

            return redirect('/')

        return wrapper

    return decorate


def no_login(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if check_logged():
            return redirect(url_for('dashboard'))

        return fun(*args, **kwargs)

    return wrapper


@app.get('/health')
def ping():
    return 'OK' if api.check_valid_conn() else 'BAD'


@app.get('/')
@no_login
def home():
    return render_template('index.html', servers=api.get_servers_names())


def _login_process(user: User, endpoint):
    logger.info(f'{endpoint}:{user}')
    resp = make_response(redirect(url_for('dashboard')))
    resp.set_cookie(SESSION_NAME, user.sessionid, httponly=True, secure=True, samesite='Lax',
                    max_age=timedelta(days=3))
    return resp


@app.post('/login')
@no_login
def login():
    req = request.form
    if req['verificationToken']:
        return passwordless_signin()
    user = api.login(req['username'].lower(), req['password'], int(req['server']), req['clan'].lower())
    if user:
        return _login_process(user, login.__name__)

    cache = {
        'username': req['username'],
        'server': int(req['server']),
        'clan': req['clan']
    }
    logger.warning(f'{login.__name__}:{cache}')

    return render_template('index.html', error='We could not find you', servers=api.get_servers_names(),
                           cache=cache), 401


@app.post('/passwordless/signin')
@no_login
def passwordless_signin():
    req = request.form
    verification_token = req['verificationToken']
    userid = api_pwl.signin_verify(verification_token)
    if userid:
        username = api.get_username_by_userid(userid)
        if username:
            user = api.login(username, skip=True)
            return _login_process(user, passwordless_signin.__name__)


@app.get('/passwordless/register')
@login_req()
def passwordless_register(user: User):
    registration_token = api_pwl.register(user)
    return jsonify({'token': registration_token, 'publicKey': os.getenv('PWL_PUBLIC_KEY')})


@app.get('/passwordless/pbk')
@no_login
def passwordless_pbk():
    return jsonify({'publicKey': os.getenv('PWL_PUBLIC_KEY')})


@app.get('/passwordless/credentials')
@login_req()
def passwordless_credentials(user: User):
    return jsonify(api_pwl.credentials(user))


@app.delete('/passwordless/delete')
@login_req()
def passwordless_delete(user: User):
    return jsonify({'deleted': api_pwl.delete_credential(request.json['credential'])})


@app.get('/logout')
@login_req()
def logout(user: User):
    return logout_fun(user.sessionid)


@app.get('/dashboard')
@login_req()
def dashboard(user: User):
    return render_template('dashboard.html', user=user, role_name=ROLES[user.role],
                           role_color=ROLES_COLORS[user.role])


@app.get('/timers-type')
@login_req()
def get_timers_type(user: User):
    return jsonify(api.get_timers_type_by_clanid(user.clanid))


@app.get('/timers/<_type>')
@login_req()
def get_timers_by_type(user: User, _type):
    return jsonify(api.get_timers_by_clanid_type(user.clanid, _type.upper()))


@app.get('/timers')
@login_req(role=3)
def get_timers(user: User):
    return jsonify(api.get_timers(user.clanid))


@app.delete('/timers')
@login_req(role=3)
def delete_timers(user: User):
    res = api.delete_timer_by_bossname(request.json['bossname'].lower(), user.clanid)
    if res:
        return jsonify(res)

    return jsonify(None), 404


@app.patch('/timers')
@login_req(role=3)
def patch_timers(user: User):
    res = api.patch_timer_by_bossname(user.clanid, request.json['bossname'].lower(),
                                      int(request.json['respawn']), int(request.json['window']))
    if res:
        return jsonify(res)

    return jsonify(None), 404


@app.patch('/timer/reset/<bossname>')
@login_req(role=1)
def reset_timer_by_bossname(user: User, bossname):
    res = api.reset_timer_by_clanid_bossname(user.clanid, bossname.lower())
    if res:
        return jsonify(res)

    return jsonify(None), 404


@app.post('/timer-add')
@login_req(role=3)
def add_timer(user: User):
    req = request.form
    res = api.add_timer(user.clanid, req['bossname'].lower(), req['type'].upper(), int(req['respawn']),
                        int(req['window']))

    if res:
        msg = {'text': f'{req["bossname"]} added', 'type': 'success'}
    else:
        msg = {'text': 'Try again, there was an error.', 'type': 'danger'}

    return render_template('clan.html', user=user, role_name=ROLES[user.role], role_color=ROLES_COLORS[user.role],
                           msg=msg, role_names=ROLES, role_colors=ROLES_COLORS)


@app.get('/profile')
@login_req(change_pw=False)
def profile(user: User):
    return render_template('profile.html', user=user, pwl_credentials=api_pwl.credentials(user),
                           role_name=ROLES[user.role],
                           role_color=ROLES_COLORS[user.role],
                           msg={'text': 'Please change your password',
                                'type': 'danger'} if user.change_pw else None)


@app.post('/change-pw')
@login_req(change_pw=False)
def change_pwd(user: User):
    req = request.form
    if 8 <= len(req['newPassword']) <= 20:
        res = api.change_pw(user.userprofileid, req['oldPassword'], req['newPassword'])
    else:
        res = None

    if res:
        msg = {'text': 'Password changed. Sessions have not been deleted, you may want to check them.',
               'type': 'success'}
    else:
        msg = {'text': 'Try again, there was an error.', 'type': 'danger'}

    return render_template('profile.html', user=user, role_name=ROLES[user.role],
                           role_color=ROLES_COLORS[user.role],
                           msg=msg)


@app.get('/clan')
@login_req(role=3)
def clan(user: User):
    return render_template('clan.html', user=user, role_name=ROLES[user.role], role_color=ROLES_COLORS[user.role],
                           role_names=ROLES, role_colors=ROLES_COLORS)


@app.post('/user-add')
@login_req(role=4)
def add_user(user: User):
    req = request.form
    role = int(req['role'])
    if 0 <= role < len(ROLES):
        res = api.add_user(user.clanid, user.serverid, req['username'].lower(), req['name'], role)
    else:
        res = None

    if res:
        msg = {'text': f'username: {req["username"]}, temporary password: {res}', 'type': 'success'}
    else:
        msg = {'text': 'Try again, there was an error.', 'type': 'danger'}

    return render_template('clan.html', user=user, role_name=ROLES[user.role], role_color=ROLES_COLORS[user.role],
                           msg=msg, role_names=ROLES, role_colors=ROLES_COLORS)


@app.get('/users')
@login_req(role=4)
def get_users(user: User):
    return jsonify(api.get_users(user.clanid))


@app.delete('/users')
@login_req(role=4)
def delete_user(user: User):
    res = api.delete_user_by_username(request.json['username'], user.clanid)
    if res:
        return jsonify(res)

    return jsonify(None), 404


@app.post('/user-role')
@login_req(role=4)
def change_user_role(user: User):
    req = request.json
    role = int(req['role'])
    if 0 <= role < len(ROLES):
        res = api.change_user_role(user.clanid, req['username'], role)
    else:
        res = None

    if res:
        return jsonify(res)

    return jsonify(None), 404


@app.get('/sessions')
@login_req()
def sessions(user: User):
    return render_template('sessions.html', user=user, role_name=ROLES[user.role],
                           role_color=ROLES_COLORS[user.role])


@app.get('/user-sessions')
@login_req()
def get_user_sessions(user: User):
    user_sessions = api.get_user_sessions(user.userprofileid)
    data = {'sessions': [], 'current': -1}
    for us in user_sessions:
        data['sessions'].append(us.get_data_select('id', 'creation', 'lastuse', 'host'))
        if us.id == user.id:
            data['current'] = us.id

    return jsonify(data)


@app.delete('/user-sessions')
@login_req()
def delete_user_sessions(user: User):
    res = api.delete_session_by_id(request.json['id'])
    if res:
        return jsonify(res)

    return jsonify(None), 404


if __name__ == '__main__':
    format_logger = '[%(time)s] %(status)s %(REQUEST_METHOD)s %(REQUEST_URI)s'
    serve(TransLogger(app, format=format_logger),
          host='0.0.0.0',
          port=8080,
          url_scheme='https',
          ident=None)
