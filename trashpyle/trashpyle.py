import cherrypy
import os
import urllib.request
import urllib.parse

class Trashpyle(object):
    SERVERPATH="http://213.168.213.236/bremereb/bify/bify.jsp?"

    @cherrypy.expose
    def index(self):
        content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trashpyle</title>
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
            </head>
            <body>
            <div class="container">
                <div class="row">
                    <div class="page-header">
                        <h1>Müllkalender Generator <small>Version 0.1</small></h1>
                    </div>
                    <div class="panel panel-default">
                    <div class="panel-body">
                    <form method="get" action="generate">
                        <p>Bitte eine Straße angeben (eine in Bremen natürlich).</p>
                        <div class="form-group">
                        <label for="streetInput">Straße</label>
                        <input type="text" name="street" class="form-control" id="streetInput" placeholder="Straße">
                        </div>

                        <div class="form-group">
                        <label for="numberInput">Hausnummer</label>
                        <input type="number" name="number" class="form-control" id="numberInput" placeholder="Hausnummer">
                        </div>

                        <button type="submit" class="btn btn-default">Müllplan generieren</button>
                    </form>
                    </div>
                    </div>
                </div>
            </div>
            </body>
            </html>
            """
        return content

    @cherrypy.expose
    def generate(self,street='',number=''):
        content = "Straße: {} {}".format(street,number)
        content += self.fetchBify(street,number)
        return content

    def fetchBify(self,street,number):
        values = {'strasse' : street,
                    'hausnummer' : number }
        headers = { 'User-Agent' : "Trashpyle", 
                    'Content-Length' : ''}
        data = urllib.parse.urlencode(values)
        req = self.SERVERPATH + data
        with urllib.request.urlopen(req) as response:
            content = response.read()
        return content


if __name__ == '__main__':
    conf = {
         '/': {
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './public'
         }
     }
    cherrypy.quickstart(Trashpyle(), '/', conf)

