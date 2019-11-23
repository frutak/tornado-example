#!/usr/bin/env python

import os
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import tornado.web
import tornado.websocket
from datetime import datetime
import tornado.wsgi
from uuid import uuid4
from time import time
import json
from hashlib import sha256


define("environment", default="development", help="Pick you environment", type=str)
define("site_title", default="Tornado Example", help="Site Title", type=str)
define("cookie_secret", default="sooooooosecret", help="Your secret cookie dough", type=str)
define("port", default="8000", help="Listening port", type=str)





seenfiles = []
myserver = 'frutak.pythonanywhere.com'
DEFAULT_PORT_HTTPS = 8443
DEFAULT_PORT_HTTP = 8080
upgrade_file_user1 = "image_user1-0x01000.bin"
upgrade_file_user2 = "image_user2-0x81000.bin"
arduino_file = "image_arduino.bin"

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello from Tornado")

class OTAUpdate(tornado.web.StaticFileHandler):
    def should_return_304(self):
        """Used as a hook to get the retrived URL's, never allow caching.
        """
        print("Sending file: %s" % self.request.path)
        seenfiles.append(str(self.request.path))
        return False

class DispatchDevice(tornado.web.RequestHandler):

    def post(self):
        # telling device where to connect to in order to establish a WebSocket
        #   channel
        # as the initial request goes to port 443 anyway, we will just continue
        #   on this port
        print("<< HTTP POST %s" % self.request.path)
        data = {
            "error": 0,
            "reason": "ok",
            "IP": myserver,
            "port": DEFAULT_PORT_HTTPS
        }
        print(">> %s" % self.request.path)
        logjson(data)
        self.write(data)
        self.finish()


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print("<< WEBSOCKET OPEN")
        # the device expects the server to generate and consistently provide
        #   an API key which equals the UUID format
        # it *must not* be the same apikey which the device uses in its
        # requests
        self.uuid = str(uuid4())
        self.setup_completed = False
        self.test = False
        self.upgrade = False
        self.stream.set_nodelay(True)
        self.device_model = "ITA-GZ1-GL"

    def on_message(self, message):
        print("<< WEBSOCKET INPUT")
        dct = json.loads(message)
        logjson(dct, False)
        # if dct.has_key("action"): # python2
        if "action" in dct:     # python3
            print("~~~ device sent action request, acknowledging / answering...")
            if dct['action'] == "register":
                # ITA-GZ1-GL, PSC-B01-GL, etc.
                if "model" in dct and dct["model"]:
                    self.device_model = dct["model"]
                    print("We are dealing with a {} model.".format(self.device_model))
                print("~~~~ register")
                data = {
                    "error": 0,
                    "deviceid": dct['deviceid'],
                    "apikey": self.uuid,
                    "config": {
                        "hb": 1,
                        "hbInterval": 145
                    }
                }
                logjson(data)
                self.write_message(data)
            if dct['action'] == "date":
                print("~~~~ date")
                data = {
                    "error": 0,
                    "deviceid": dct['deviceid'],
                    "apikey": self.uuid,
                    "date": datetime.isoformat(datetime.today())[:-3] + 'Z'
                }
                logjson(data)
                self.write_message(data)
            if dct['action'] == "query":
                print("~~~~ query")
                data = {
                    "error": 0,
                    "deviceid": dct['deviceid'],
                    "apikey": self.uuid,
                    "params": 0
                }
                logjson(data)
                self.write_message(data)
            if dct['action'] == "update":
                print("~~~~ update")
                data = {
                    "error": 0,
                    "deviceid": dct['deviceid'],
                    "apikey": self.uuid
                }
                logjson(data)
                self.write_message(data)
                self.setup_completed = True
        # elif dct.has_key("sequence") and dct.has_key("error"): # python2
        elif "sequence" in dct and "error" in dct:
            print(
                "~~~ device acknowledged our action request (seq {}) "
                "with error code {}".format(
                    dct['sequence'],
                    dct['error'] # 404 here
                )
            )
            if dct['error'] == 404:
                self.upgrade = True
        else:
            print("## MOEP! Unknown request/answer from device!")

        if self.setup_completed and not self.test:
            # switching relais on and off - for fun and profit!
            data = {
                "action": "update",
                "deviceid": dct['deviceid'],
                "apikey": self.uuid,
                "userAgent": "app",
                "sequence": str(int(time() * 1000)),
                "ts": 0,
                "params": {
                    "switch": "off"
                },
                "from": "hackepeter"
            }
            logjson(data)
            self.write_message(data)
            data = {
                "action": "update",
                "deviceid": dct['deviceid'],
                "apikey": self.uuid,
                "userAgent": "app",
                "sequence": str(int(time() * 1000)),
                "ts": 0,
                "params": {
                    "switch": "on"
                },
                "from": "hackepeter"
            }
            logjson(data)
            self.write_message(data)
            data = {
                "action": "update",
                "deviceid": dct['deviceid'],
                "apikey": self.uuid,
                "userAgent": "app",
                "sequence": str(int(time() * 1000)),
                "ts": 0,
                "params": {
                    "switch": "off"
                },
                "from": "hackepeter"
            }
            logjson(data)
            self.write_message(data)
            data = {
                "action": "update",
                "deviceid": dct['deviceid'],
                "apikey": self.uuid,
                "userAgent": "app",
                "sequence": str(int(time() * 1000)),
                "ts": 0,
                "params": {
                    "switch": "on"
                },
                "from": "hackepeter"
            }
            logjson(data)
            self.write_message(data)
            data = {
                "action": "update",
                "deviceid": dct['deviceid'],
                "apikey": self.uuid,
                "userAgent": "app",
                "sequence": str(int(time() * 1000)),
                "ts": 0,
                "params": {
                    "switch": "off"
                },
                "from": "hackepeter"
            }
            logjson(data)
            self.write_message(data)
            self.test = True

        if self.setup_completed and self.test and not self.upgrade:

            hash_user1 = self.getFirmwareHash(upgrade_file_user1)
            hash_user2 = self.getFirmwareHash(upgrade_file_user2)


            if hash_user1 and hash_user2:
                udir = 'ota'
                data = {
                    "action": "upgrade",
                    "deviceid": dct['deviceid'],
                    "apikey": self.uuid,
                    "userAgent": "app",
                    "sequence": str(int(time() * 1000)),
                    "ts": 0,
                    "params": {
                        # the device expects two available images, as the original
                        #   firmware splits the flash into two halfs and flashes
                        #   the inactive partition (ping-pong).
                        # as we don't know which partition is (in)active, we
                        # provide our custom image as user1 as well as user2.
                        # unfortunately this also means that our firmware image
                        # must not exceed FLASH_SIZE / 2 - (bootloader - spiffs)
                        "binList": [
                            {
                                "downloadUrl": "http://%s:%s/%s/%s" %
                                (myserver, DEFAULT_PORT_HTTP, udir, upgrade_file_user1),
                                # the device expects and checks the sha256 hash of
                                #   the transmitted file
                                "digest": hash_user1,
                                "name": "user1.bin"
                            },
                            {
                                "downloadUrl": "http://%s:%s/%s/%s" %
                                (myserver, DEFAULT_PORT_HTTP, udir, upgrade_file_user2),
                                # the device expects and checks the sha256 hash of
                                #   the transmitted file
                                "digest": hash_user2,
                                "name": "user2.bin"
                            }
                        ],
                        # if `model` is set to sth. else (I tried) the websocket
                        #   gets closed in the middle of the JSON transmission
                        "model": self.device_model,
                        # the `version` field doesn't seem to have any effect;
                        #   nevertheless set it to a ridiculously high number
                        #   to always be newer than the existing firmware
                        "version": "23.42.5"
                    }
                }
                logjson(data)
                self.write_message(data)
                self.upgrade = True

    def on_close(self):
        print("~~ websocket close")

    def getFirmwareHash(self, filePath):
        hash_user = None
        try:
            with open(filePath, "rb") as firmware:
                hash_user = sha256(firmware.read()).hexdigest()
        except IOError as e:
            print(e)
        return hash_user



application = tornado.wsgi.WSGIApplication([
    (r"/", MainHandler),
    # handling initial dispatch HTTPS POST call to eu-disp.coolkit.cc
    (r'/dispatch/device', DispatchDevice),
    # handling actual payload communication on WebSockets
    (r'/api/ws', WebSocketHandler),
    (r'/ota/(.*)', OTAUpdate, {'path': "static/"}),
])


def logjson(data, outbound=True):
    if outbound:
        direction = '>>'
    else:
        direction = '<<'
    if 'password' in data:
        # Don't update original dict
        data = dict(data)
        data['password'] = '*' * len(data['password'])
    print("{} {}".format(direction, json.dumps(data, indent=4)))



class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
           (r"/", MainHandler),
           (r"/([^/]+)", FourOhFourHandler),
        ]
        settings = dict(
            site_title=options.site_title,
            cookie_secret=options.cookie_secret,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    print "Server listening on port " + str(options.port)
    logging.getLogger().setLevel(logging.DEBUG)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
