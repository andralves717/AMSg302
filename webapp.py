import cherrypy
import os
import sqlite3
import json
import requests
from sqlite3 import Error
from jinja2 import Environment, PackageLoader, select_autoescape


class WebApp(object):
    database = 'baseDados.db'

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('webapp', 'html'),
            autoescape=select_autoescape(['html', 'xml'])
        )

    # Utilities
    def db_connection(self, dbFile):
        try:
            connect = sqlite3.connect(dbFile)
            return connect
        except Error as e:
            print(e)
        return None

    def render(self, tpg, tps):
        template = self.env.get_template(tpg)
        return template.render(tps)

    # User authentication
    def set_user(self, username=None):
        if username == None:
            cherrypy.session['user'] = {'authenticated': False, 'username': ''}
        else:
            cherrypy.session['user'] = {'authenticated': True, 'username': username}

    def get_user(self):
        if not 'user' in cherrypy.session:
            self.set_user()
        return cherrypy.session['user']

    def user_authenticationDB(self, username, password):
        user = self.get_user()
        db_con = self.db_connection(WebApp.database)
        command = "select password from utilizadores where username ==('{}') ".format(username)
        cur = db_con.execute(command)
        linha = cur.fetchone()
        if linha != None:
            if linha[0] == password:
                self.set_user(username)
        db_con.close()

    def createUserDB(self, username, password, email):
        db_con = self.db_connection(WebApp.database)
        command = "insert into utilizadores (username, password, email) values ('{}','{}','{}')".format(username,
                                                                                                        password, email)
        try:
            cur = db_con.execute(command)
            db_con.commit()
            db_con.close()
        except sqlite3.Error as e:
            return False
        return True

    # templates
    @cherrypy.expose()
    def index(self):
        tparams = {
            'title': 'Home',
            'user': self.get_user(),
            'errors': False
        }
        return self.render("index.html",tparams)

    @cherrypy.expose
    def login(self, username=None, password=None):
        if username is None:
            tparams = {
                'title': 'Login',
                'user': self.get_user(),
                'errors': False
            }
            return self.render('login.html', tparams)
        else:
            self.user_authenticationDB(username, password)
            if not self.get_user()['authenticated']:
                tparams = {
                    'title': 'Home',
                    'user': self.get_user(),
                    'errors': True,
                }
                return self.render('login.html', tparams)
            else:
                print("oiiiiiiiiii")
                raise cherrypy.HTTPRedirect("/my_events")

    @cherrypy.expose
    def signUp(self, username=None, password=None, email=None):
        if username is None:
            tparams = {
                'title': 'Sign Up',
                'user': self.get_user(),
                'errors': False,
            }
            return self.render('signUp.html', tparams)
        else:
            done = self.createUserDB(username, password, email)
            if done:
                cherrypy.HTTPRedirect("/index")
            tparams = {
                'title': 'Sign Up',
                'user': self.get_user(),
                'errors': True,
            }
            return self.render('signUp.html', tparams)

    @cherrypy.expose()
    def my_events(self):
        tparams = {
            'title': 'My Events',
            'errors': False,
            'user': self.get_user(),
            # 'events': events_list
        }
        return self.render('my_events.html', tparams)

    @cherrypy.expose()
    def create_event(self, name=None, s_date=None, e_date=None, place=None, modality=None, max_participants=None):
        tparams = {
            'title': 'Create Event',
            'errors': False,
            'user': self.get_user(),
        }
        return self.render('create_event.html', tparams)

    @cherrypy.expose()
    def event_details(self):
        tparams = {
            'title': 'Event Details',
            'errors': False,
            'user': self.get_user(),
            # 'information': event_info
        }
        return self.render('event_details.html', tparams)


if __name__ == '__main__':
    baseDir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.log("CityRunning Project")
    cherrypy.log("Dir is " + str(baseDir))
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': baseDir
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        },
    }

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    app = WebApp()
    cherrypy.quickstart(app, '/', conf)
