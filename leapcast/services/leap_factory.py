from __future__ import unicode_literals

import subprocess
import copy
import logging
import tempfile
import shutil

import tornado.websocket
import tornado.ioloop
import tornado.web

from leapcast.services.websocket import App
from leapcast.utils import render
from leapcast.environment import Environment


class Browser(object):
    def __init__(self, appurl):
        args = [
            Environment.chrome,
            '--allow-running-insecure-content',
            '--no-default-browser-check',
            '--ignore-gpu-blacklist',
            '--incognito',
            '--no-first-run',
            '--kiosk',
            '--disable-translate',
            '--user-agent=%s' % Environment.user_agent.encode('utf8')
        ]
        self.tmpdir = tempfile.mkdtemp(prefix='leapcast-')
        args.append('--user-data-dir=%s' % self.tmpdir)
        if Environment.window_size:
            args.append('--window-size=%s' % Environment.window_size)
        if not Environment.fullscreen:
            args.append('--app=%s' % appurl.encode('utf8'))
        else:
            args.append(appurl.encode('utf8'))
        logging.debug(args)
        self.pid = subprocess.Popen(args)

    def destroy(self):
        self.pid.terminate()
        self.pid.wait()
        shutil.rmtree(self.tmpdir)

    def is_running(self):
        return self.pid.poll() is None

    def __bool__(self):
        return self.is_running()


class LEAPfactory(tornado.web.RequestHandler):
    application_status = dict(
        name='',
        state='stopped',
        link='',
        browser=None,
        connectionSvcURL='',
        protocols='',
        app=None
    )

    service = '''<?xml version='1.0' encoding='UTF-8'?>
    <service xmlns='urn:dial-multiscreen-org:schemas:dial'>
        <name>{{ name }}</name>
        <options allowStop='true'/>
        {% if state == "running" %}
        <servicedata xmlns='urn:chrome.google.com:cast'>
            <connectionSvcURL>{{ connectionSvcURL }}</connectionSvcURL>
            <protocols>
                {% for x in protocols %}
                <protocol>{{ x }}</protocol>
                {% end %}
            </protocols>
        </servicedata>
        {% end %}
        <state>{{ state }}</state>
        {% if state == "running" %}
        <activity-status xmlns="urn:chrome.google.com:cast">
          <description>{{ name }} Receiver</description>
        </activity-status>
        <link rel='run' href='web-1'/>
        {% end %}
    </service>
    '''

    ip = None
    url = '{{query}}'
    supported_protocols = ['ramp']
    clients = 0

    def get_name(self):
        return self.__class__.__name__

    def get_status_dict(self):
        status = copy.deepcopy(self.application_status)
        status['name'] = self.get_name()
        return status

    def prepare(self):
        self.ip = self.request.host

    def get_app_status(self):

        stat = Environment.global_status.get(self.get_name(),
                                             self.get_status_dict())
        return stat

    def set_app_status(self, app_status):

        app_status['name'] = self.get_name()
        Environment.global_status[self.get_name()] = app_status

    def _response(self):
        self.set_header('Content-Type', 'application/xml')
        self.set_header(
            'Access-Control-Allow-Method', 'GET, POST, DELETE, OPTIONS')
        self.set_header('Access-Control-Expose-Headers', 'Location')
        self.set_header('Cache-control', 'no-cache, must-revalidate, no-store')
        self.finish(self._toXML(self.get_app_status()))

    @tornado.web.asynchronous
    def post(self, sec):
        '''Start app'''
        self.clear()
        self.set_status(201)
        self.clients += 1
        print 'before', self._headers.get('Location')
        self.set_header('Location', self._getLocation(self.get_name()))
        print 'after', self._headers['Location']
        self.start_app(True)
        self.finish()

    def start_app(self, run_browser):
        status = self.get_app_status()
        import requests
        if status['browser'] is None:
            status['state'] = 'running'
            query = self.request.body if self.request else None
            appurl = render(self.url).generate(query=query)
            status['browser'] = Browser(appurl) if run_browser else False
            status['connectionSvcURL'] = 'http://%s/connection/%s' % (
                self.ip, self.get_name())
            status['protocols'] = self.supported_protocols
            status['app'] = App.get_instance(self.get_name())
            self.set_app_status(status)

            Environment.global_status['screen_id'] = None
        else:
            if not Environment.global_status.get('screen_id'):
                Environment.global_status['screen_id'] = raw_input('enter screen id: ').strip()

            # There's a youtube-specific serverside pairing that needs to
            # happen before devices connect.
            # This is handled automatically by the browser when opening the appurl,
            # but opening another appurl will result in two separate casting sessions.
            # So, we manually pair any other clients.
            # Presumably the clients will do this automatically if the youtube
            # session is advertised properly.
            import urlparse
            import pprint
            print 'incoming:'
            pprint.pprint(self.request.__dict__)
            print
            pairing_code = urlparse.parse_qs(self.request.body)['pairingCode'][0]
            postdata = (
                "access_type=permanent&app=lb-v4&pairing_code=%s&screen_id=%s" %
                (pairing_code, Environment.global_status['screen_id'])
            )
            print 'sending:'
            print postdata
            res = requests.post(
                'https://www.youtube.com/api/lounge/pairing/register_pairing_code',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                },
                data=postdata,
            )
            print 'result:'
            print res
            print repr(res.content)

            """
            https://www.youtube.com' -H 'accept-encoding: gzip, deflate' -H 'accept-language:
            en-US,en;q=0.8' -H 'cookie: gh_music_feed_tab=true; VISITOR_INFO1_LIVE=IO9g7tDadU8;
            YSC=nBn8xtS5t64;
            SID=DQAAABgBAABittTf6uWLeNtkBk3vvll5LMVBCOlsUORrsHbAB-S-DjM6def-vluxfq4goBTfG9Q6K-Ex1aKdJXKYy8jppecBBo-8voL23YGGv_XuSwJG7xUyaPkt_Uvu_Rx_puAFAxGW7QAUqSVc9po69v4gPKIEX0kybktro5HEJCck-3E3jkykWYPOQbxcpHHbML8yXMotmj1pZ9i37n8e9YCMDwGRLNKVUVK_WhbToeIUiZWo2Jt0QbDOXN7Fp5srXJBmjYSghPBxcghxFWqeEZmI3yqC2uqp4YKK1vCxNUlAOJmct8EVsauJfD-pQVpawNz3egBdFmfaaVQdXxWUYDQ3aASqVYbwWU6eZliJnP9_3pRtPEdrcoL5agCkH_GPQtw0leE;
            HSID=AGXInGccAUwWUoQ7Q; SSID=ALNVmnXQ2w13D3rp7;
            APISID=K-PAOyF3WGMzT_7G/AqLXTiogr1swmjjty; SAPISID=9DTo7DVodYdsC7Ra/AeCMdcPycWNOyKZj5;
            LOGIN_INFO=e417ff8ac81cf7c7abf732327010c24ec2oAAAB7IjQiOiAiR0FJQSIsICI3IjogMTQxOTcyMTE3NCwgIjEiOiAxLCAiMyI6IDc0Mjg5NzIwOSwgIjIiOiAidFpSU0dEZ0lXbXY3WnZUQk1CcTVFZz09IiwgIjgiOiAzNDA3NDQ5MTkxNTl9;
            ACTIVITY=1419901904194; PREF=fv=16.0.0&f5=30&f4=4000000&al=en&f1=50000000;
            Oeb7d.resume=PtB5vDxIoy4:3061,bV_57YhCs20:497,TpXHo-BuPNQ:914;
            S=youtube_lounge_remote=HdfaJ2wXpX1L7uZEFO41BA' -H 'x-client-data:
            CKS1yQEIhbbJAQiltskBCKm2yQEIxLbJAQjxiMoBCPaTygE=' -H 'user-agent: Mozilla/5.0
            (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko)
            Chrome/39.0.2171.95 Safari/537.36'
            -H 'accept: */*' -H 'referer: https://www.youtube.com/tv?amp=&amp=' -H 'dnt: 1' --data
            --compressed
            """

    def stop_app(self):
        self.clear()
        browser = self.get_app_status()['browser']
        if browser is not None:
            browser.destroy()
        else:
            logging.warning('App already closed in destroy()')
        status = self.get_status_dict()
        status['state'] = 'stopped'
        status['browser'] = None

        self.set_app_status(status)

    @tornado.web.asynchronous
    def get(self, sec):
        '''Status of an app'''
        self.clear()
        browser = self.get_app_status()['browser']
        if not browser:
            logging.debug('App crashed or closed')
            # app crashed or closed
            status = self.get_status_dict()
            status['state'] = 'stopped'
            status['browser'] = None
            self.set_app_status(status)

        self._response()

    @tornado.web.asynchronous
    def delete(self, sec):
        '''Close app'''
        self.stop_app()
        self._response()

    def _getLocation(self, app):
        return 'http://%s/apps/%s/web-1' % (self.ip, app)

    def _toXML(self, data):
        xml = render(self.service).generate(**data)
        print '--->>>'
        print xml
        print '<<<---'
        print
        return xml

    @classmethod
    def toInfo(cls):
        data = copy.deepcopy(cls.application_status)
        data['name'] = cls.__name__
        data = Environment.global_status.get(cls.__name__, data)
        return render(cls.service).generate(data)
