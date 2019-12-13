import cherrypy
import os
import sqlite3
from sqlite3 import Error
from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import date


# event_details cherrypy.expose()

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
        if username is None:
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

    def create_eventDB(self, name=None, s_date=None, e_date=None, place=None, modality=None, max_participants=None):
        username = self.get_user()['username']
        command = "insert into eventos values ('{}','{}','{}','{}','{}','{}','{}','{}')".format(username, name, s_date,
                                                                                                e_date, place,
                                                                                                max_participants, "",
                                                                                                modality)
        db_con = self.db_connection(WebApp.database)
        try:
            cur = db_con.execute(command)
            db_con.commit()
            db_con.close()
        except sqlite3.Error as e:
            return False
        return True

    def get_events(self):
        nome = self.get_user()['username']
        command_event = "select * from eventos where gestor =('{}') ".format(nome)
        db_con = self.db_connection(WebApp.database)
        cur = db_con.execute(command_event)
        tabela = cur.fetchall()

        lista = []
        for evento in tabela:
            event = {'nome': evento[1], 'inicio': evento[2], 'fim': evento[3], 'place': evento[4],
                     'modality': evento[7]}
            lista.append(event)

        command_event = "select * from eventos where registrations like '%{}%'".format(nome)
        db_con = self.db_connection(WebApp.database)
        cur = db_con.execute(command_event)
        tabela = cur.fetchall()

        for evento in tabela:
            event = {'nome': evento[1], 'inicio': evento[2], 'fim': evento[3], 'place': evento[4],
                     'modality': evento[7]}
            if event not in lista:
                lista.append(event)

        db_con.close()
        return lista

    def get_event_details(self, nameEvent):
        comand = "select * from eventos where nome = ('{}')".format(nameEvent)
        db_con = self.db_connection(WebApp.database)
        cur = db_con.execute(comand)
        evento = cur.fetchone()
        db_con.close()

        registrations = self.get_registrations(nameEvent)

        details = {'gestor': evento[0], 'nome': evento[1], 'inicio': evento[2], 'fim': evento[3], 'place': evento[4],
                   'maxPart': evento[5], 'modality': evento[7], 'numRegistrations': len(registrations),
                   'registrations': registrations}

        username = self.get_user()['username']
        if username == details['gestor']:  # ver se é gestor
            return details, True
        else:
            return details, False

    def get_registrations(self, nameEvent, string=False):
        comand = "select * from eventos where nome = ('{}')".format(nameEvent)
        db_con = self.db_connection(WebApp.database)
        cur = db_con.execute(comand)
        reg = cur.fetchall()[0]
        db_con.close()
        registrations = reg[-2]
        if string:
            if registrations ==[]:
                return ""
            else:
                return registrations
        lista = registrations.split(";")
        if '' in lista:
            lista.remove('')
        lista_strings = [s.strip('()') for s in lista]
        lista_of_listas = [l.split(',') for l in lista_strings]
        return lista_of_listas

    def add_resultDb(self, event_name, participant, result):
        db_con = self.db_connection(self.database)
        command = "insert into resultados values ('{}','{}','{}','{}')".format(event_name, participant, result,
                                                                               date.today())
        try:
            db_con.execute(command)
            db_con.commit()
            db_con.close()
        except sqlite3.Error:
            return False
        return True

    def get_results(self, event_name):
        db_con = self.db_connection(self.database)
        command = "select * from resultados where evento_nome = ('{}')".format(event_name)
        cur = db_con.execute(command)
        tabela = cur.fetchall()
        db_con.close()

        results = [{'username': result[1], 'result': result[2], 'date': result[3]} for result in tabela]
        return results

    def edit_eventDB(self, arg_alter, new_arg, event_name):
        username = self.get_user()['username']
        db_con = self.db_connection(self.database)
        command = "UPDATE eventos SET '{}'='{}' WHERE nome='{}' and gestor = '{}'".format(arg_alter, new_arg,
                                                                                          event_name, username)
        try:
            db_con.execute(command)
            db_con.commit()
            db_con.close()
            return False
        except sqlite3.Error:
            return True

    def delete_eventDB(self, event_name):
        db_con = self.db_connection(self.database)
        username = self.get_user()['username']
        command = "delete from eventos where nome='{}' and gestor='{}'".format(event_name, username)
        try:
            db_con.execute(command)
            db_con.commit()
            db_con.close()
            return False
        except sqlite3.Error:
            return True

    def add_particant(self, name, email, event_name):
        db_con = self.db_connection(self.database)
        registrations = self.get_registrations(event_name, True)
        registrations += "(" + name + "," + email + ")" + ";"
        command = "update eventos set registrations='{}' where nome = '{}'".format(registrations, event_name)
        try:
            db_con.execute(command)
            db_con.commit()
            db_con.close()
            return False
        except sqlite3.Error:
            return True

    def get_search_events(self, query):
        command = "select * from eventos where nome like '%{}%' or place like '%{}%' or modality like '%{}%'".format(query, query, query)
        db_con = self.db_connection(self.database)
        cur = db_con.execute(command)
        lista = cur.fetchall()
        eventos = []
        for evento in lista:
            event = {'nome': evento[1], 'inicio': evento[2], 'fim': evento[3], 'place': evento[4],
                     'modality': evento[7]}
            eventos.append(event)
        db_con.close()
        return eventos


    # templates
    @cherrypy.expose()
    def index(self):
        tparams = {
            'title': 'Home',
            'user': self.get_user(),
            'errors': False
        }
        return self.render("index.html", tparams)

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
        if not self.get_user()['authenticated']:
            raise cherrypy.HTTPRedirect('/')
        else:
            events_list = self.get_events()
            tparams = {
                'title': 'My Events',
                'errors': False,
                'user': self.get_user(),
                'events': events_list
            }
            return self.render('my_events.html', tparams)

    @cherrypy.expose()
    def create_event(self, name=None, s_date=None, e_date=None, place=None, modality=None, max_participants=None):
        if name is None:
            tparams = {
                'title': 'Create Event',
                'errors': False,
                'user': self.get_user(),
            }
            return self.render('create_event.html', tparams)
        done = self.create_eventDB(name, s_date, e_date, place, modality, max_participants)
        if not done:
            tparams = {
                'title': 'Create Event',
                'errors': True,
                'user': self.get_user(),
            }
            return self.render('create_event.html', tparams)
        else:
            tparams = {
                'title': 'Create Event',
                'errors': False,
                'user': self.get_user(),
            }
            raise cherrypy.HTTPRedirect('/my_events')

    @cherrypy.expose()
    def event_details(self, nameEvent=None):
        event_info, isGestor = self.get_event_details(nameEvent)
        user = self.get_user()
        isInscrito = False
        usernames = [d[0] for d in event_info['registrations']]
        if user['username'] in usernames:
            isInscrito = True
        tparams = {
            'title': 'Event Details',
            'errors': False,
            'user': user,
            'information': event_info,
            'isGestor': isGestor,
            'isInscrito': isInscrito
        }
        return self.render('event_details.html', tparams)

    @cherrypy.expose()
    def add_registration(self, name=None, email=None, nameEvent=None):
        tparams = {
            'title': 'Registration',
            'errors': False,
            'user': self.get_user(),
            'nameEvent': nameEvent
        }
        if not nameEvent or not name or not email:
            return self.render('add_registration.html', tparams)
        else:
            error = self.add_particant(name, email, nameEvent)
            if error:
                tparams['errors'] = True
                return self.render('add_registration.html', tparams)
            else:
                raise cherrypy.HTTPRedirect('/event_details?nameEvent=' + nameEvent)

    @cherrypy.expose()
    def add_results(self, name=None, result=None, nameEvent=None, automatic=None):
        tparams = {
            'title': 'Add Results',
            'errors': False,
            'user': self.get_user(),
            'nameEvent': nameEvent
        }

        if not nameEvent or not automatic:
            return self.render('add_results.html', tparams)
        else:
            if automatic == "True":
                print('Buscar aos sensores'.center(50, '-'))
            else:
                self.add_resultDb(nameEvent, name, result)
            # raise cherrypy.HTTPRedirect('/event_details?nameEvent='+nameEvent)
            return self.render('add_results.html', tparams)

    @cherrypy.expose()
    def edit_event(self, new_arg=None, arg2change=None, nameEvent=None):
        tparams = {
            'title': 'Edit Event',
            'errors': False,
            'user': self.get_user(),
            'nameEvent': nameEvent
        }
        if not new_arg or not arg2change:
            return self.render('edit_event.html', tparams)
        else:
            error = self.edit_eventDB(arg2change, new_arg, nameEvent)
            if error:
                tparams = {
                    'title': 'Edit Event',
                    'errors': True,
                    'user': self.get_user(),
                    'nameEvent': nameEvent
                }
                return self.render('edit_event.html', tparams)
            if arg2change == 'nome':
                raise cherrypy.HTTPRedirect('/event_details?nameEvent=' + new_arg)
            else:
                raise cherrypy.HTTPRedirect('/event_details?nameEvent=' + nameEvent)

    @cherrypy.expose()
    def delete_event(self, nameEvent=None):
        self.delete_eventDB(nameEvent)
        raise cherrypy.HTTPRedirect('/my_events')

    @cherrypy.expose()
    def see_registrations(self, nameEvent):
        participants = self.get_registrations(nameEvent)

        tparams = {
            'title': 'Registrations',
            'errors': False,
            'user': self.get_user(),
            'nameEvent': nameEvent,
            'participants': participants
        }
        return self.render('see_registrations.html', tparams)

    @cherrypy.expose()
    def see_results(self, nameEvent):
        results = self.get_results(nameEvent)
        tparams = {
            'title': 'Results',
            'errors': False,
            'user': self.get_user(),
            'nameEvent': nameEvent,
            'results': results
        }
        return self.render('see_results.html', tparams)
    @cherrypy.expose()
    def search(self, query):
        eventos = self.get_search_events(query)
        tparams = {
            'title': 'My Events',
            'errors': False,
            'user': self.get_user(),
            'events': eventos
        }
        return self.render('search.html',tparams)

    # Error page
def error_page(status, message, traceback, version):
    tparams = {
        'status'    : status,
        'message'   : message,
        'traceback' : traceback,
        'version'   : version
    }
    return app.render('error.html', tparams)


if __name__ == '__main__':
    baseDir = os.path.dirname(os.path.abspath(__file__))
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

    
    cherrypy.config.update({'error_page.400': error_page})
    cherrypy.config.update({'error_page.404': error_page})      
    cherrypy.config.update({'error_page.500': error_page})  

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    # cherrypy.config.update({'server.socket_port': 8080})

    app = WebApp()
    cherrypy.quickstart(app, '/', conf)
