import cherrypy
import os
from jinja2 import Environment, PackageLoader, select_autoescape

class WebApp(object):

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('webapp', 'html'),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, tpg, tps):
        template = self.env.get_template(tpg)
        return template.render(tps)
    @cherrypy.expose
    def index(self):
        tparams = {
            'title': 'Login'
        }
        return self.render('login.html', tparams)

    @cherrypy.expose
    def signUp(self):
        tparams = {
            'title': 'Sign up'
        }
        return self.render('signUp.html',tparams)




if __name__ == '__main__':
    baseDir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.log("CityRunning Project")
    cherrypy.log("Dir is " + str(baseDir))
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': baseDir
        },
        '/utils': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './utils'
        },
    }


    cherrypy.config.update({'server.socket_host' : '127.0.0.1'})
    cherrypy.config.update({'server.socket_port' : 8080})

    app = WebApp()
    cherrypy.quickstart(app,'/',conf)