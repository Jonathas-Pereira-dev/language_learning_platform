import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
import app

class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.old = app.DB
        app.DB = Path(cls.tmp.name) / 'test.sqlite3'
        app.init_db()
        cls.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        app.DB = cls.old
        cls.tmp.cleanup()

    def setUp(self):
        self.cookie = ''

    def request(self, path, data=None, cookie=None, origin=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type':'application/json', 'Cookie':self.cookie if cookie is None else cookie}
        if origin:
            headers['Origin'] = origin
        c.request('GET' if data is None else 'POST', path, None if data is None else json.dumps(data), headers)
        r = c.getresponse()
        if r.getheader('Set-Cookie'):
            self.cookie = r.getheader('Set-Cookie').split(';')[0]
        raw, status = r.read(), r.status
        c.close()
        return status, json.loads(raw) if path.startswith('/api/') else raw

    def register(self, email):
        self.assertEqual(self.request('/api/register', {'name':'Ana','email':email,'password':'senha-segura123'})[0],200)

    def test_learning_flow_and_isolation(self):
        self.assertEqual(self.request('/api/state')[0],401)
        self.register('ana@example.com')
        first = self.cookie
        self.assertNotIn('answer',self.request('/api/state')[1]['lessons'][0]['questions'][0])
        self.assertEqual(self.request('/api/diagnostic',{'answers':[0,1,2,0,1],'goal':'Viagem','daily':15})[1]['level'],'B1')
        self.assertEqual(self.request('/api/submit',{'lesson':'saludos','answers':[1]})[0],400)
        self.assertEqual(self.request('/api/submit',{'lesson':'saludos','answers':[1,2,0]})[1]['score'],3)
        state = self.request('/api/state')[1]
        self.assertEqual(len(state['attempts']),1)
        self.assertEqual(len(state['reviews']),3)
        card = state['reviews'][0]['id']
        self.request('/api/review',{'id':card,'remembered':True})
        self.assertEqual(len(self.request('/api/state')[1]['reviews']),2)
        self.request('/api/notes',{'lesson':'saludos','text':'Mi nota'})
        self.assertEqual(self.request('/api/state')[1]['notes']['saludos'],'Mi nota')
        self.register('outra@example.com')
        self.assertEqual(self.request('/api/state')[1]['attempts'],[])
        self.assertEqual(self.request('/api/review',{'id':card,'remembered':True})[0],400)
        self.cookie = first
        self.request('/api/logout',{})
        self.assertEqual(self.request('/api/state',cookie=first)[0],401)
        self.assertEqual(self.request('/api/login',{'email':'ana@example.com','password':'errada'})[0],401)
        self.assertEqual(self.request('/api/login',{'email':'ana@example.com','password':'senha-segura123'})[0],200)
        self.assertEqual(self.request('/api/state')[1]['notes']['saludos'],'Mi nota')

    def test_static_and_input_protection(self):
        self.assertEqual(self.request('/')[0],200)
        self.assertEqual(self.request('/../app.py')[0],404)
        self.assertEqual(self.request('/api/register',{'name':'Ana','email':'x','password':'1'})[0],400)
        self.assertEqual(self.request('/api/register',{},origin='https://other.example')[0],403)

if __name__ == '__main__':
    unittest.main()
