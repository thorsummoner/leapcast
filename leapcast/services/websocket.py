# -*- coding: utf8 -*-

from __future__ import unicode_literals
from collections import deque
import json
import logging
from leapcast.environment import Environment
from volume import get_volume_controller
import tornado.web
import threading
from __builtin__ import id

import tornado.web

from leapcast.environment import Environment


class App(object):
    '''
    Used to relay messages between app Environment.channels
    '''
    name = ""
    lock = threading.Event()
    remotes = list()
    receivers = list()
    rec_queue = list()
    buf = {}  # Buffers if the channel are not ready
    control_channel = list()
    senderid = False
    info = None

    @classmethod
    def get_instance(cls, app):

        if app in Environment.channels:
            return Environment.channels[app]
        else:
            instance = App()
            instance.name = app
            Environment.channels[app] = instance
            return instance

    def set_control_channel(self, ch):
        logging.info("Channel for app set to %s", ch)
        self.control_channel.append(ch)

    def get_control_channel(self):
        try:
            logging.info("Channel for app is %s", self.control_channel[-1])
            return self.control_channel[-1]
        except Exception:
            return False

    def get_apps_count(self):
        return len(self.remotes)

    def add_remote(self, remote):
        self.remotes.append(remote)

    def add_receiver(self, receiver):
        self.receivers.append(receiver)
        if id(receiver) in self.buf:
            self.rec_queue.append(self.buf[id(receiver)])
        else:
            self.rec_queue.append(deque())

    def get_deque(self, instance):
        try:
            _id = self.receivers.index(instance)
            return self.rec_queue[_id]
        except Exception:
            if id(instance) in self.buf:
                return self.buf[id(instance)]
            else:
                self.buf[id(instance)] = deque()
                return self.buf[id(instance)]

    def get_app_channel(self, receiver):
        try:
            return self.remotes[self.receivers.index(receiver)]
        except Exception:
            return False

    def get_self_app_channel(self, app):
        try:
            if isinstance(self.remotes[self.remotes.index(app)].ws_connection,
                          type(None)):
                return False
            return self.remotes[self.remotes.index(app)]
        except Exception:
            return False

    def get_recv_channel(self, app):
        try:
            """
            if type(self.receivers[self.remotes.index(app)].ws_connection) != type(None):
                return self.receivers[self.remotes.index(app)]
            """
            if isinstance(
                    self.receivers[self.remotes.index(app)].ws_connection,
                    type(None)):
                return False
            return self.receivers[self.remotes.index(app)]
        except Exception:
            return False

    def create_application_channel(self, data):
        if self.get_control_channel():
            self.get_control_channel().new_request()
        else:
            CreateChannel(self.name, data, self.lock).start()

    def stop(self):
        for ws in self.remotes:
            try:
                ws.close()
            except Exception:
                pass
        self.remotes = list()
        for ws in self.receivers:
            try:
                ws.close()
            except Exception:
                pass
        self.receivers = list()
        self.control_channel.pop()
        app = Environment.global_status.get(self.name, False)
        if app:
            app.stop_app()
        self.buf = {}


class CreateChannel(threading.Thread):
    def __init__(self, name, data, lock):
        threading.Thread.__init__(self)
        self.name = name
        self.data = data
        self.lock = lock

    def run(self):
        # self.lock.wait(30)
        self.lock.clear()
        self.lock.wait()
        App.get_instance(
            self.name).get_control_channel().new_request(self.data)


class ServiceChannel(tornado.websocket.WebSocketHandler):
    '''
    ws /connection
    From 1st screen app
    '''
    buf = list()

    def open(self, app=None):
        self.app = App.get_instance(app)
        self.app.set_control_channel(self)
        while len(self.buf) > 0:
            self.reply(self.buf.pop())

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        cmd = json.loads(message)
        if cmd["type"] == "REGISTER":
            self.app.lock.set()
            self.app.info = cmd

        if cmd["type"] == "CHANNELRESPONSE":
            self.new_channel()

    def reply(self, msg):
        if isinstance(self.ws_connection, type(None)):
            self.buf.append(msg)
        else:
            self.write_message((json.dumps(msg)))

    def new_channel(self):
        logging.info("NEWCHANNEL for app %s" % (self.app.info["name"]))
        ws = "ws://localhost:8008/receiver/%s" % self.app.info["name"]
        self.reply(
            {
                "type": "NEWCHANNEL",
                "senderId": self.senderid,
                "requestId": self.app.get_apps_count(),
                "URL": ws
            }
        )

    def new_request(self, data=None):
        logging.info("CHANNELREQUEST for app %s" % (self.app.info["name"]))
        if data:
            try:
                data = json.loads(data)
                self.senderid = data["senderId"]
            except Exception:
                self.senderid = self.app.get_apps_count()
        else:
            self.senderid = self.app.get_apps_count()

        self.reply(
            {
                "type": "CHANNELREQUEST",
                "senderId": self.senderid,
                "requestId": self.app.get_apps_count(),
            }
        )

    def on_close(self):
        self.app.stop()


class WSC(tornado.websocket.WebSocketHandler):
    def open(self, app=None):
        self.app = App.get_instance(app)
        self.cname = self.__class__.__name__

        logging.info("%s opened %s" %
                     (self.cname, self.request.uri))

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        if Environment.verbosity is logging.DEBUG:
            if not ('ping' in message or 'pong' in message):
                pretty = json.loads(message)
                message = json.dumps(
                    pretty, sort_keys=True, indent=2)
                logging.debug("%s: %s" % (self.cname, message))

    def on_close(self):
        if self.app.name in Environment.channels:
            del Environment.channels[self.app.name]
        logging.info("%s closed %s" %
                     (self.cname, self.request.uri))


class ReceiverChannel(WSC):
    '''
    ws /receiver/$app
    From 1st screen app
    '''

    def open(self, app=None):
        super(ReceiverChannel, self).open(app)
        self.app.add_receiver(self)

        queue = self.app.get_deque(self)
        while len(queue) > 0:
            self.on_message(queue.pop())

    def on_message(self, message):
        channel = self.app.get_app_channel(self)
        if channel:
            queue = self.app.get_deque(self)
            while len(queue) > 0:
                self.on_message(queue.pop())

            super(ReceiverChannel, self).on_message(message)
            channel.write_message(message)
        else:
            queue = self.app.get_deque(self)
            queue.append(message)

    def on_close(self):
        channel = self.app.get_app_channel(self)
        try:
            self.app.receivers.remove(self)
        except:
            pass

        if channel:
            channel.on_close()


class ApplicationChannel(WSC):
    '''
    ws /session/$app
    From 2nd screen app
    '''

    def ping(self):
        self.app.get_deque(self)

        channel = self.app.get_self_app_channel(self)
        if channel:
            data = json.dumps(["cm", {"type": "ping", "cmd_id": 0}])
            channel.write_message(data)
            # TODO Magic number -- Not sure what the interval should be, the
            # value of `pingInterval` is 0.
            threading.Timer(5, self.ping).start()

    def open(self, app=None):
        super(ApplicationChannel, self).open(app)
        self.app.add_remote(self)
        self.app.get_deque(self)

        self.ping()

    def on_message(self, message):
        channel = self.app.get_recv_channel(self)
        if channel:
            queue = self.app.get_deque(self)
            while len(queue) > 0:
                self.on_message(queue.pop())

            super(ApplicationChannel, self).on_message(message)
            channel.write_message(message)
        else:
            queue = self.app.get_deque(self)
            queue.append(message)

    def on_close(self):
        channel = self.app.get_recv_channel(self)
        try:
            self.app.remotes.remove(self)
        except:
            pass

        if channel:
            channel.on_close()


class CastPlatform(WSC):
    '''
    Remote control over WebSocket.

    Commands are:
    {u'type': u'GET_VOLUME', u'cmd_id': 1}
    {u'type': u'GET_MUTED', u'cmd_id': 2}
    {u'type': u'VOLUME_CHANGED', u'cmd_id': 3}
    {u'type': u'SET_VOLUME', u'cmd_id': 4}
    {u'type': u'SET_MUTED', u'cmd_id': 5}

    Device control:

    '''

    def check_origin(self, origin):
        # Accept all connections for now...
        return True

    def __init__(self, *args, **kwargs):
        super(CastPlatform, self).__init__(*args, **kwargs)
        self._vctrl = get_volume_controller()

    def _write_error(self, request):
        response = dict(
            success=False,
            cmd_id=request["cmd_id"],
            type=request["type"]
        )
        self.write_message(json.dumps(response))

    def on_message(self, message):
        # TODO This seems to work OK for now, but someone should verify the protocol with an actual device.

        if Environment.verbosity is logging.DEBUG:
            pretty = json.loads(message)
            message = json.dumps(
                pretty, sort_keys=True, indent=2)
            logging.debug("CastPlatform: %s" % message)

        request = json.loads(message)

        def implies(a, b):
            return (not a) or b

        assert "cmd_id" in request, "Request is missing cmd_id"
        assert "type" in request, "Request is missing type"
        assert implies(request["type"] == "SET_VOLUME", "level" in request), "Request is missing level"
        assert implies(request["type"] == "SET_MUTE", "muted" in request), "Request is missing muted"

        if self._vctrl is None:
            self._write_error(request)
            return

        if request["type"] == "SET_VOLUME":
            logging.debug("Setting volume to %f" % request["level"])
            self._vctrl.set_volume(request["level"])

        elif request["type"] == "SET_MUTED":
            logging.debug("Muting volume %s" % request["muted"])
            self._vctrl.set_muted(request["muted"])

        elif request["type"] == "GET_VOLUME":
            logging.debug("Getting volume")

        elif request["type"] == "GET_MUTED":
            logging.debug("Getting mute")

        else:
            logging.error("Unknown request type: %s" % request["type"])
            self._write_error(request)

        v = self._vctrl.get_volume()
        m = self._vctrl.is_muted()
        response = dict(
            success=True,
            cmd_id=request["cmd_id"],
            type=request["type"],
            level=v,
            muted=m
        )
        self.write_message(json.dumps(response))
