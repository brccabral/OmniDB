#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'OmniDB.settings'
import django
django.setup()
import sys
import html.parser
import http.cookies
import OmniDB
import OmniDB.settings
import django.template.defaulttags
import django.template.loader_tags
import OmniDB_app
import OmniDB_app.apps
import django.contrib.staticfiles
import django.contrib.staticfiles.apps
import django.contrib.admin.apps
import django.contrib.auth.apps
import django.contrib.contenttypes.apps
import django.contrib.sessions.apps
import django.contrib.messages.apps
import OmniDB_app.urls
import django.contrib.messages.middleware
import django.contrib.auth.middleware
import django.contrib.sessions.middleware
import django.contrib.sessions.serializers
import django.template.loaders
import django.contrib.auth.context_processors
import django.contrib.messages.context_processors
import psycopg2

from django.core.handlers.wsgi import WSGIHandler
from OmniDB import user_database, ws_core, ws_chat

import logging
import logging.config
import optparse
import time

from django.contrib.sessions.backends.db import SessionStore

from cefpython3 import cefpython as cef

import socket
import random

import configparser
import urllib.request

logger = logging.getLogger('OmniDB_app.Init')

def check_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        return False
    s.close()
    return True

def check_page(port):
    try:
        code = urllib.request.urlopen("http://localhost:{0}".format(port)).getcode()
        if code == 200:
            return True
        else:
            return False
    except Exception as exc:
        return False

def init_browser(server_port):
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    cef.CreateBrowserSync(url="http://localhost:{0}?user=admin&pwd=admin".format(str(server_port)),window_title="OmniDB")
    cef.MessageLoop()
    cef.Shutdown()

if __name__ == "__main__":
    #default port

    parser = optparse.OptionParser(version=OmniDB.settings.OMNIDB_VERSION)
    parser.add_option("-p", "--port", dest="port",
                      default=None, type=int,
                      help="listening port")

    parser.add_option("-c", "--configfile", dest="conf",
                      default=OmniDB.settings.CONFFILE, type=str,
                      help="configuration file")

    parser.add_option("-w", "--wschatport", dest="chatport",
                      default=OmniDB.settings.WS_CHAT_PORT, type=int,
                      help="chat port")

    (options, args) = parser.parse_args()

    #Choosing empty port
    port = options.chatport
    num_attempts = 0

    print('''Starting Chat websocket...''')
    logger.info('''Starting Chat websocket...''')
    print('''Checking port availability...''')
    logger.info('''Checking port availability...''')

    while not check_port(port) or num_attempts >= 20:
        print("Port {0} is busy, trying another port...".format(port))
        logger.info("Port {0} is busy, trying another port...".format(port))
        port = random.randint(1025,32676)
        num_attempts = num_attempts + 1

    if num_attempts < 20:
        OmniDB.settings.WS_CHAT_PORT = port

        print ("Starting chat websocket server at port {0}.".format(str(port)))
        logger.info("Starting chat websocket server at port {0}.".format(str(port)))

        #Websocket Chat
        ws_chat.start_wsserver_thread()
    else:
        print('Tried 20 different ports without success, closing...')
        logger.info('Tried 20 different ports without success, closing...')

    #Parsing config file
    Config = configparser.ConfigParser()
    Config.read(options.conf)
    if not os.path.exists(options.conf):
        print("Config file not found, using default settings.")

    if options.port!=None:
        listening_port = options.port
    else:
        try:
            listening_port = Config.getint('webserver', 'listening_port')
        except:
            listening_port = OmniDB.settings.OMNIDB_DEFAULT_APP_PORT

    #Choosing empty port
    port = listening_port
    num_attempts_port = 0

    print('''Starting OmniDB server...''')
    logger.info('''Starting OmniDB server...''')
    print('''Checking port availability...''')
    logger.info('''Checking port availability...''')

    while not check_port(port) or num_attempts_port >= 20:
        print("Port {0} is busy, trying another port...".format(port))
        logger.info("Port {0} is busy, trying another port...".format(port))
        port = random.randint(1025,32676)
        num_attempts_port = num_attempts_port + 1

    if num_attempts_port < 20:
        OmniDB.settings.OMNIDB_PORT          = port
        OmniDB.settings.TORNADO_SERVE_DJANGO = True

        print ("Starting server at port {0}.".format(str(port)))
        logger.info("Starting server at port {0}.".format(str(port)))

        #Removing Expired Sessions
        SessionStore.clear_expired()

        # User Database
        user_database.work()

        #Websocket Core
        ws_core.start_wsserver_thread()

        #Wait until webserver is ready to start browser
        num_attempts_page = 0
        webserver_working = False
        time.sleep(0.5)

        while not check_page(port) or num_attempts_page >= 20:
            print("Webserver is not ready yet. Trying again...")
            logger.info("Webserver is not ready yet. Trying again...")
            time.sleep(0.5)

        if num_attempts_page < 20:
            init_browser(port)
        else:
            print('Checked 20 times and webserver is still not responding, closing...')
            logger.info('Checked 20 times and webserver is still not responding, closing...')

    else:
        print('Tried 20 different ports without success, closing...')
        logger.info('Tried 20 different ports without success, closing...')
