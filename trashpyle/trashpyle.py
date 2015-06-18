#/usr/bin/python3
# -*- coding: utf-8 -*-

import cherrypy
import os
import urllib.parse
import re
import urllib.request
from bs4 import BeautifulSoup
from enum import Enum
from datetime import datetime,timedelta,date
from icalendar import Calendar, Event, vDate, Alarm
from cherrypy.process.plugins import Daemonizer
d = Daemonizer(cherrypy.engine)
d.subscribe()

class TrashType(Enum):
    unbekannt = 0
    papier_gelber_sack = 1
    restmuell = 2
    tannenbaum = 3
    
class Trashpyle(object):
    SERVERPATH="http://213.168.213.236/bremereb/bify/bify.jsp"

    @cherrypy.expose
    def index(self):
        content = """
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta charset="utf-8"/>
                <title>Trashpyle</title>
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
            </head>
            <body>
            <div class="container">
                <div class="row">
                    <div class="page-header">
                        <h1>Müllkalender Generator <small>trashpyle - Version 0.1</small></h1>
                    </div>
                    <div class="panel panel-default">
                    <div class="panel-body">
                    <p>
                    Da die EKO (Entsorgung Kommunal) aus Bremen die Abfallkalender leider nur als PDF und als Java-Applet bereit stellt, habe ich diesen
                    Kalender-Generator gebaut. Du kannst hier den Abfallkalender für deine Straße im iCalendar-Format (*.ics) generieren und herunterladen.
                    Dieses Format wird von den meisten Kalendarprogrammen verstanden. Du kannst dir auch einen Alarm mit in die Datei schreiben lassen, damit
                    du ein paar Stunden vorher informiert wirst.
                    </p>
                    <p>Der Code liegt wie immer auf Github - <a href="https://github.com/bitstacker/trashpyle">https://github.com/bitstacker/trashpyle</a></p>
                    <p>Fehler und Verbesserungsvorschläge bitte ebenfalls auf Github posten - <a href="https://github.com/bitstacker/trashpyle/issues">
                    https://github.com/bitstacker/trashpyle/issues</a></p>
                    <p><a href="https://blog.never-afk.de/">blog.never-afk.de</a> <i>bitstacker (at) never-afk.de</i></p>
                    </div>
                    </div>
                    <div class="panel panel-default">
                    <div class="panel-body">
                    <form method="get" action="linkpage">
                        <p>Bitte eine Straße angeben (eine in Bremen natürlich).</p>
                        <div class="form-group">
                        <label for="streetInput">Straße</label>
                        <input type="text" name="street" class="form-control" id="streetInput" placeholder="Straße">
                        </div>

                        <div class="form-group">
                        <label for="numberInput">Hausnummer</label>
                        <input type="number" name="number" class="form-control" id="numberInput" placeholder="Hausnummer">
                        </div>
                        
                        <div class="form-group">
                        <label for="alarmInput">Wie viele Minuten vorher soll benachrichtigt werden? (Feld leer lassen für keine Benachrichtigung)</label>
                        <input type="number" name="alarm" class="form-control" id="alarmInput" placeholder="Minuten">
                        </div>

                        <button type="submit" class="btn btn-default"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span>
                         Müllplan generieren</button>
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
    def linkpage(self,street='',number='',alarm=''):
        if street == '' or number == '':
            content = """
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta charset="utf-8"/>
                <title>Trashpyle</title>
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
            </head>
            <body>
            <div class="container">
                <div class="row">
                    <div class="page-header">
                        <h1>Müllkalender Generator <small>trashpyle - Version 0.1</small></h1>
                    </div>
                    <div class="alert alert-danger" role="alert">Straße oder Hausnummer nicht angegeben.</div>
                </div>
            </div>
            </body>
            </html>

            """
        else:
            content = """
                <!DOCTYPE html>
                <html lang="de">
                <head>
                    <meta charset="utf-8"/>
                    <title>Trashpyle</title>
                    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                </head>
                <body>
                <div class="container">
                    <div class="row">
                        <div class="page-header">
                            <h1>Müllkalender Generator <small>trashpyle - Version 0.1</small></h1>
                        </div>
                        <div class="panel panel-default">
                        <div class="panel-body">
                        <p>
                        Du findest deinen Kalender unter folgendem Link:
                """
            content += '<a href="generate?street='+street+'&number='+number+'&alarm='+alarm+'">'
            content += 'Kalender herunterladen</a>'
            content += """
                        </p>
                        <p>
                        <a class="btn btn-default" href="/" role="button">Zum Formular zurück</a>
                        </p>
                        </div>
                        </div>
                    </div>
                </div>
                </body>
                </html>
                """
        return content

    @cherrypy.expose
    def generate(self,street='',number='',alarm=''):
        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="muell.ics"'
        bify = self.fetchBifyForStreetAndNumber(street,number)
        eventlist = self.findTrashEventsInContent(bify)
        content = self.getiCalFromEventlist(eventlist,alarm)
        return content

    def fetchBifyForStreetAndNumber(self,street,number):
        street = urllib.parse.quote(street,encoding="ISO-8859-1")
        number = urllib.parse.quote(number,encoding="ISO-8859-1")
        url = "http://213.168.213.236/bremereb/bify/bify.jsp?strasse={}&hausnummer={}".format(street,number)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            content = response.read()
        content = content.decode("ISO-8859-1")
        content = content.replace("<nobr><br>","</nobr>")#Hack for parsing siblings
        return content

    def findTrashEventsInContent(self,content):
        soup = BeautifulSoup(content)
        eventlist = []
        
        for month in soup.find_all("b",text=re.compile("^\w+\s\d{4}")):
            current_year = self.getYearFromMonthString(month.string)
            for sibling in month.find_next_siblings("nobr",text=re.compile("^(\(\w{2}\)\s)?\d{2}\.\d{2}\.\s")):
                current_date = self.getDateObjectFromEventString(current_year,sibling.string)
                trashtype = self.getTrashTypeFromEventString(sibling.string)
                eventlist.append([current_date,str(trashtype)])
        return eventlist
    
    def getYearFromMonthString(self, month_s):
        year = month_s.split(" ")[1]
        return year

    def getDateObjectFromEventString(self, current_year, date_s):
        date_s = self.cutDayNoticeWhenNeeded(date_s)
        complete_string = date_s.split()[0] + current_year
        the_datetime = datetime.strptime(complete_string,"%d.%m.%Y")
        the_date = date(the_datetime.year,the_datetime.month,the_datetime.day)
        return the_date

    def cutDayNoticeWhenNeeded(self,date_s):
        matcher = re.compile("^\(\w{2}\)\s") # For (Sa),(Fr) etc.
        if matcher.match(date_s):
            date_s = date_s[5:]
        return date_s

    def getTrashTypeFromEventString(self, event_s):
        event_s = self.cutDayNoticeWhenNeeded(event_s)
        trash_string = event_s[7:]
        if trash_string in ["Restmüll / Bioabfall","Restm. / Bioabf."]:
            trashtype = TrashType.restmuell
        elif trash_string in ["Papier / Gelber Sack","Papier / G.Sack"]:
            trashtype = TrashType.papier_gelber_sack
        elif trash_string == "Tannenbaumabfuhr":
            trashtype = TrashType.tannenbaum
        else:
            trashtype = TrashType.unbekannt
        return trashtype

    def getiCalFromEventlist(self, eventlist, alarm):
        cal = Calendar()
        cal.add('prodid', 'trashpyle')
        cal.add('version', '0.1')
        for event in eventlist:
            icalevent = Event()
            icalevent.add('dtstart', event[0])
            icalevent.add('dtend', event[0] + timedelta(days=1))
            icalevent.add('summary', self.getNameStringFromTrashType(event[1]))
            if alarm != '':
                alarmtime = timedelta(minutes=-int(alarm))
                icalalarm = Alarm()
                icalalarm.add('action','DISPLAY')
                icalalarm.add('trigger',alarmtime)
                icalevent.add_component(icalalarm)
            cal.add_component(icalevent)
        return cal.to_ical()

    def getNameStringFromTrashType(self, trashtype):
        trashname = ""
        if trashtype == 'TrashType.restmuell':
            trashname = "Restmüll / Bioabfall"
        elif trashtype == 'TrashType.papier_gelber_sack':
            trashname = "Papier / Gelber Sack"
        elif trashtype == 'TrashType.tannenbaum':
            trashname = "Tannenbaumabfuhr"
        else:
            trashname = "Unbekannt"
        return trashname


conf = {
     '/': {
         'tools.staticdir.root': os.path.abspath(os.getcwd())
     },
     '/static': {
         'tools.staticdir.on': True,
         'tools.staticdir.dir': './public'
     }
 }
cherrypy.server.socket_host = '127.0.0.1'
cherrypy.server.socket_port = 8080
cherrypy.quickstart(Trashpyle(), '/', conf)

