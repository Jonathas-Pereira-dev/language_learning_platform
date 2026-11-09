import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
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

    def test_invited_password_activation(self):
        import hashlib
        from datetime import timedelta
        token = 'private-first-access-token'
        with app.connect() as con:
            uid = con.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',
                              ('Invited', 'invited@example.com', app.password_hash('unavailable-password'), 'teacher')).lastrowid
            con.execute('INSERT INTO resets VALUES(?,?,?)',
                        (hashlib.sha256(token.encode()).hexdigest(), uid,
                         (app.now() + timedelta(days=1)).isoformat()))
            con.execute("INSERT OR REPLACE INTO access_settings VALUES('registration_closed','1')")
        try:
            self.assertEqual(self.request('/api/register', {'name':'Other','email':'blocked@example.com','password':'password123'})[0], 403)
            self.assertEqual(self.request('/api/reset-password', {'token':'wrong','password':'new-password123'})[0], 400)
            self.assertEqual(self.request('/api/reset-password', {'token':token,'password':'new-password123'})[0], 200)
            self.assertEqual(self.request('/api/reset-password', {'token':token,'password':'another-password123'})[0], 400)
            self.assertEqual(self.request('/api/login', {'email':'invited@example.com','password':'new-password123'})[0], 200)
            self.assertEqual(self.request('/api/state')[1]['profile']['role'], 'teacher')
        finally:
            with app.connect() as con:
                con.execute("DELETE FROM access_settings WHERE key='registration_closed'")

    def diagnose(self):
        student_cookie=self.cookie
        email=self.request('/api/state')[1]['profile']['email']
        with app.connect() as con:
            student=con.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            mentor=con.execute('SELECT * FROM users WHERE id=?',(student['teacher_id'],)).fetchone()
        if not mentor:
            self.assertEqual(self.request('/api/register',{'name':'Tutor','email':'tutor-'+email,'password':'senha-segura123','role':'teacher'})[0],200)
            mentor_cookie=self.cookie
            invite=self.request('/api/state')[1]['profile']['invite']
            self.cookie=student_cookie
            self.request('/api/join',{'code':invite})
            self.cookie=mentor_cookie
        else:
            self.assertEqual(self.request('/api/login',{'email':mentor['email'],'password':'senha-segura123','role':'teacher'})[0],200)
        self.assertEqual(self.request('/api/diagnostic-authorize',{'student_id':student['id']})[0],200)
        self.cookie=student_cookie
        self.assertEqual(self.request('/api/diagnostic-start',{})[0],200)
        current=self.request('/api/state')[1]
        answers=[next(q['answer'] for q in app.DIAGNOSTIC if q['id']==p['id']) for p in current['diagnostic']]
        return self.request('/api/diagnostic',{'round_id':current['diagnostic_round_id'],'answers':answers})[1]

    def test_learning_flow_and_isolation(self):
        self.assertEqual(self.request('/api/state')[0],401)
        self.register('ana@example.com')
        first = self.cookie
        self.assertNotIn('answer',self.request('/api/state')[1]['lessons'][0]['questions'][0])
        self.assertEqual(self.diagnose()['level'],'C2')
        self.assertEqual(self.request('/api/submit',{'lesson':'saludos','answers':[1]})[0],400)
        self.assertNotIn('score',self.request('/api/submit',{'lesson':'saludos','answers':[1,2,0],'written':['Hola, me llamo Ana. ¿Cómo estás?','Uso mucho gusto al conocer a alguien.']})[1])
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

    def test_teacher_student_permissions_and_feedback(self):
        self.request('/api/register', {'name':'Professora','email':'teacher@example.com','password':'senha-segura123','role':'teacher'})
        teacher_cookie=self.cookie
        invite=self.request('/api/state')[1]['profile']['invite']
        self.register('mentee@example.com')
        student_cookie=self.cookie
        self.assertEqual(self.request('/api/activities',{})[0],403)
        self.assertEqual(self.request('/api/join',{'code':invite})[0],200)
        self.diagnose()
        self.cookie=teacher_cookie
        student=self.request('/api/state')[1]['students'][0]
        self.assertEqual(student['diagnostics'][0]['level'],'C2')
        self.assertEqual(student['goal'],'Viagem')
        self.assertEqual(student['daily'],15)
        self.assertEqual(len(student['placement_dates']),1)
        self.assertEqual(student['content_history'],[])
        activity={'title':'No hotel','instructions':'Resolva sua reserva','audio':'Hola, tengo una reserva.','tasks':['Apresente-se','Peça ajuda','Confirme a reserva'],'resource':'https://example.com/aula'}
        self.assertEqual(self.request('/api/activities',activity)[0],200)
        activity_id=self.request('/api/state')[1]['activities'][0]['id']
        self.cookie=student_cookie
        self.assertEqual(self.request('/api/activity-submit',{'activity_id':activity_id,'answers':['Hola','Necesito ayuda','Gracias']})[0],200)
        student_state=self.request('/api/state')[1]
        self.assertEqual(student_state['students'],[])
        submission_id=student_state['submissions'][0]['id']
        self.assertEqual(self.request('/api/feedback',{'submission_id':submission_id,'feedback':'fake'})[0],403)
        self.cookie=teacher_cookie
        self.assertEqual(self.request('/api/feedback',{'submission_id':submission_id,'feedback':'Pratique confirmar as datas.'})[0],200)
        self.assertEqual(self.request('/api/message',{'recipient':student['id'],'text':'Vamos conversar na próxima aula.'})[0],200)
        self.register('outsider@example.com')
        self.assertEqual(self.request('/api/activity-submit',{'activity_id':activity_id,'answers':['a','b','c']})[0],403)
        self.assertEqual(self.request('/api/message',{'recipient':student['id'],'text':'Intrusão'})[0],403)
        self.cookie=student_cookie
        result=self.request('/api/state')[1]
        self.assertEqual(result['submissions'][0]['feedback'],'Pratique confirmar as datas.')
        self.assertEqual(len(result['messages']),1)

    def test_diagnostic_sequential_and_reset_revocation(self):
        from learning import assess
        import hashlib
        self.register('reset@example.com')
        old_cookie=self.cookie
        answers=[q['answer'] for q in app.DIAGNOSTIC]
        answers[:3]=[-1,-1,-1]
        self.assertEqual(assess(answers)['level'],'Pré-A1')
        with app.connect() as con:
            uid=con.execute('SELECT id FROM users WHERE email=?',('reset@example.com',)).fetchone()['id']
            con.execute('INSERT INTO resets VALUES(?,?,?)',(hashlib.sha256(b'test-token').hexdigest(),uid,(app.now()+app.timedelta(minutes=30)).isoformat()))
        self.assertEqual(self.request('/api/reset-password',{'token':'test-token','password':'nova-senha123'})[0],200)
        self.assertEqual(self.request('/api/state',cookie=old_cookie)[0],401)
        self.assertEqual(self.request('/api/reset-password',{'token':'test-token','password':'outra-senha123'})[0],400)
        self.assertEqual(self.request('/api/login',{'email':'reset@example.com','password':'nova-senha123'})[0],200)

    def test_ai_context_and_audio_records(self):
        self.register('conversation@example.com')
        response=MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps({'choices':[{'message':{'content':json.dumps({'reply':'¿Cuántas noches?','feedback':['Use tengo una reserva.']})}}]}).encode()
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test-secret','OPENAI_MODEL':'test-model'}), patch('mentoring.urlopen',return_value=response) as call:
            self.assertEqual(self.request('/api/conversation',{'scenario':'hotel','message':'Yo tengo reserva'})[0],200)
            self.assertEqual(self.request('/api/conversation',{'scenario':'hotel','message':'Dos noches'})[0],200)
            sent=json.loads(call.call_args.args[0].data)
            self.assertEqual(len(sent['messages']),4)
            self.assertEqual(sent['messages'][1]['content'],'Yo tengo reserva')
        self.assertEqual(self.request('/api/audio-practice',{'track':'saludos','answers':['Hola','Buenos días','Hola Ana']})[0],200)
        with app.connect() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM chats WHERE message='Dos noches'").fetchone()[0],1)
            self.assertEqual(con.execute("SELECT count(*) FROM events WHERE kind='audio_practice'").fetchone()[0],1)

    def test_personal_form_and_diagnostic_are_separate(self):
        self.request('/api/register',{'name':'Tutor','email':'profile-teacher@example.com','password':'senha-segura123','role':'teacher'})
        teacher=self.cookie
        code=self.request('/api/state')[1]['profile']['invite']
        self.assertEqual(self.request('/api/personal-form',{})[0],403)
        self.register('profile-student@example.com')
        self.request('/api/join',{'code':code})
        values={'name':'Ana Silva','email':'contato@example.com','goal':'Trabalho','daily':30,'studied':'Já estudei','experience':'Um ano em curso','motivation':'Participar de reuniões','challenges':'Compreensão oral'}
        self.assertEqual(self.request('/api/personal-form',values)[0],200)
        result=self.request('/api/state')[1]
        self.assertIsNotNone(result['personal_form']['completed'])
        self.assertEqual(result['profile']['diagnosed'],0)
        self.assertEqual(result['profile']['email'],'profile-student@example.com')
        proof=self.diagnose()
        self.assertNotIn('score',proof)
        self.assertNotIn('details',proof)
        result=self.request('/api/state')[1]
        self.assertEqual(result['profile']['goal'],'Trabalho')
        self.assertEqual(result['profile']['daily'],30)
        self.cookie=teacher
        student=self.request('/api/state')[1]['students'][0]
        self.assertEqual(student['personal_form']['experience'],'Um ano em curso')
        self.assertEqual(student['diagnostics'][0]['level'],'C2')
        self.assertIn('weighted',student['diagnostics'][0])
        self.register('profile-outsider@example.com')
        self.assertIsNone(self.request('/api/state')[1]['personal_form'])
        self.assertEqual(self.request('/api/state')[1]['students'],[])

    def test_authorized_random_bank_and_oral_privacy(self):
        from audio_content import AUDIO_TRACKS
        self.assertEqual(len(app.DIAGNOSTIC),100)
        self.assertEqual(len({q['prompt'] for q in app.DIAGNOSTIC}),100)
        self.assertGreaterEqual(len(AUDIO_TRACKS),17)
        self.assertTrue(all(len(t['phrases'])>=15 for t in AUDIO_TRACKS))
        self.request('/api/register',{'name':'Tutor','email':'random-teacher@example.com','password':'senha-segura123','role':'teacher'})
        mentor_cookie=self.cookie
        code=self.request('/api/state')[1]['profile']['invite']
        self.register('random-student@example.com')
        pupil=self.cookie
        self.assertEqual(self.request('/api/diagnostic-start',{})[0],403)
        self.assertEqual(self.request('/api/state')[1]['diagnostic'],[])
        self.request('/api/join',{'code':code})
        with app.connect() as con:sid=con.execute('SELECT id FROM users WHERE email=?',('random-student@example.com',)).fetchone()[0]
        self.assertEqual(self.request('/api/diagnostic-authorize',{'student_id':sid})[0],403)
        self.cookie=mentor_cookie
        self.assertEqual(self.request('/api/diagnostic-authorize',{'student_id':sid})[0],200)
        self.assertEqual(self.request('/api/diagnostic-authorize',{'student_id':sid})[0],409)
        self.cookie=pupil
        self.assertEqual(self.request('/api/diagnostic-start',{})[0],200)
        first=self.request('/api/state')[1]
        self.assertEqual(len(first['diagnostic']),18)
        self.assertTrue(all(set(q)=={'id','prompt','options'} for q in first['diagnostic']))
        self.request('/api/diagnostic-start',{})
        self.assertEqual(first['diagnostic'],self.request('/api/state')[1]['diagnostic'])
        payload={'round_id':first['diagnostic_round_id'],'answers':[-1]*18}
        self.assertEqual(self.request('/api/diagnostic',payload)[0],200)
        self.assertEqual(self.request('/api/diagnostic',payload)[0],403)
        self.cookie=mentor_cookie
        self.request('/api/diagnostic-authorize',{'student_id':sid})
        self.cookie=pupil
        self.request('/api/diagnostic-start',{})
        second=self.request('/api/state')[1]
        self.assertFalse({q['id'] for q in first['diagnostic']}&{q['id'] for q in second['diagnostic']})
        self.assertEqual(self.request('/api/oral-practice',{'scenario':'hotel','text':'Tengo una reserva.'})[0],200)
        oral_id=self.request('/api/state')[1]['oral_practices'][0]['id']
        self.cookie=mentor_cookie
        self.assertEqual(self.request('/api/oral-feedback',{'id':oral_id,'feedback':'Añade una pregunta para continuar.'})[0],200)
        self.register('random-outsider@example.com')
        self.assertEqual(self.request('/api/state')[1]['oral_practices'],[])
        self.assertEqual(self.request('/api/oral-feedback',{'id':oral_id,'feedback':'Otra persona'})[0],403)
        self.cookie=pupil
        self.assertEqual(self.request('/api/state')[1]['oral_practices'][0]['feedback'],'Añade una pregunta para continuar.')
        self.assertEqual(self.request('/api/review-practice',{'kind':'grammar','id':'ser','answer':'soy'})[1]['correct'],True)

    def test_automatic_content_flashcards_and_catalog(self):
        self.request('/api/register',{'name':'Tutor','email':'cards-teacher@example.com','password':'senha-segura123','role':'teacher'})
        mentor=self.cookie
        code=self.request('/api/state')[1]['profile']['invite']
        content={'title':'Reserva de hotel','instructions':'Practica la reserva.','audio':'Recepcionista: Buenas tardes.\nCliente: Tengo una reserva para dos noches.','tasks':['Comprende','Responde','Continúa'],'resource':''}
        status,result=self.request('/api/activities',content)
        self.assertEqual(status,200)
        self.assertEqual(result['flashcard_count'],2)
        self.assertEqual(len(self.request('/api/state')[1]['activities'][0]['flashcards']),2)
        self.register('cards-student@example.com')
        pupil=self.cookie
        self.assertEqual(self.request('/api/state')[1]['activity_flashcards'],[])
        self.request('/api/join',{'code':code})
        result=self.request('/api/state')[1]
        self.assertEqual(len(result['activity_flashcards']),2)
        self.assertGreaterEqual(len(result['conversation_catalog']),30)
        self.assertTrue(all(s['level']=='A1' for s in result['conversation_catalog']))
        card=next(c for c in result['activity_flashcards'] if 'noches' in c['front'])
        self.assertEqual(card['source'],'Reserva de hotel')
        self.assertEqual(self.request('/api/review-practice',{'kind':'activity','id':card['id'],'answer':'noches'})[1]['correct'],True)
        self.assertEqual(self.request('/api/review-practice',{'kind':'activity','id':card['id'],'answer':card['front']})[1]['correct'],True)
        self.cookie=mentor
        self.request('/api/activities',{**content,'title':'Nueva actividad','audio':'Necesito cambiar la fecha.'})
        self.cookie=pupil
        self.assertEqual(len(self.request('/api/state')[1]['activity_flashcards']),3)
        self.register('cards-outsider@example.com')
        self.assertEqual(self.request('/api/review-practice',{'kind':'activity','id':card['id'],'answer':'noches'})[0],400)

    def test_podcast_cache_sources_and_validation(self):
        self.register('podcast-student@example.com')
        sample=[dict(title='Titular de prueba',url='https://example.com/noticia',publisher='Medio de prueba',published=app.now().isoformat())]
        with patch('podcasts.fetch_news',return_value=sample) as fetch:
            status,result=self.request('/api/podcasts',{'country':'MX','topic':'educacion','level':'A1'})
            self.assertEqual(status,200)
            self.assertEqual(result['items'][0]['publisher'],'Medio de prueba')
            self.assertIn('Titular de prueba',result['items'][0]['script'])
            self.assertFalse(result['stale'])
            self.assertEqual(self.request('/api/podcasts',{'country':'MX','topic':'educacion','level':'C2'})[0],403)
            with app.connect() as con:con.execute("UPDATE users SET level='C2' WHERE email='podcast-student@example.com'")
            second=self.request('/api/podcasts',{'country':'MX','topic':'educacion','level':'C2'})[1]
            self.assertNotEqual(result['items'][0]['tasks'],second['items'][0]['tasks'])
            self.assertEqual(fetch.call_count,1)
        self.assertEqual(self.request('/api/podcasts',{'country':'invalid','topic':'educacion','level':'A1'})[0],400)
        with patch('podcasts.fetch_news',side_effect=OSError('offline')):
            self.assertEqual(self.request('/api/podcasts',{'country':'CL','topic':'turismo','level':'B1'})[0],503)

    def test_progression_review_delivery_and_video_access(self):
        self.request('/api/register',{'name':'Tutor','email':'levels-teacher@example.com','password':'senha-segura123','role':'teacher'})
        mentor=self.cookie;code=self.request('/api/state')[1]['profile']['invite']
        self.request('/api/activities',{'title':'Reserva A2','level':'A2','instructions':'Explica el cambio.','audio':'Quisiera cambiar la fecha.','tasks':['Comprende','Responde','Continúa'],'resource':''})
        activity_id=self.request('/api/state')[1]['activities'][0]['id']
        video={'title':'Acentos para la clase','country':'GT','topic':'acentos','level':'A2','url':'https://example.com/video','instructions':'Compara dos expresiones.'}
        self.assertEqual(self.request('/api/videos',video)[0],200)
        with app.connect() as con:con.execute("UPDATE video_resources SET availability='available',checked_at=? WHERE url=?",(app.now().isoformat(),video['url']))
        self.register('levels-student@example.com');pupil=self.cookie
        self.request('/api/join',{'code':code})
        current=self.request('/api/state')[1]
        self.assertEqual(current['available_levels'],['A1'])
        self.assertEqual(current['activity_flashcards'],[])
        self.assertEqual(current['activities'],[])
        self.assertTrue(all(v['level']=='A1' for v in current['audio_tracks']))
        self.assertTrue(all(v['level']=='A1' for v in current['videos']))
        self.assertGreaterEqual(len(current['conversation_catalog']),30)
        self.assertTrue(all(v['level']=='A1' for v in current['conversation_catalog']))
        self.assertEqual(self.request('/api/podcasts',{'country':'ES','topic':'economia','level':'A2'})[0],403)
        self.assertEqual(self.request('/api/oral-practice',{'scenario':'viajes-0-C2','text':'Hola.'})[0],403)
        self.assertEqual(self.request('/api/activity-submit',{'activity_id':activity_id,'answers':['a','b','c']})[0],403)
        review=self.request('/api/review-practice',{'kind':'grammar','id':'ser','answer':'soy'})[1]
        self.assertTrue(review['sent_to_teacher'])
        self.cookie=mentor
        student=self.request('/api/state')[1]['students'][0]
        self.assertEqual(student['review_submissions'][0]['answer'],'soy')
        self.assertIn('Brasil',student['review_submissions'][0]['prompt'])
        with app.connect() as con:
            con.execute('INSERT INTO events(user_id,kind,payload,created) VALUES(?,?,?,?)',(student['id'],'review_practice',json.dumps({'kind':'grammar','answer':'está','expected':'está','correct':True}),app.now().isoformat()))
        app.init_db();app.init_db()
        recovered=self.request('/api/state')[1]['students'][0]['review_submissions']
        self.assertEqual(len(recovered),2,'old answers are recovered once, without duplication')
        self.assertEqual(self.request('/api/student-level',{'student_id':student['id'],'level':'A2'})[0],200)
        self.cookie=pupil;current=self.request('/api/state')[1]
        self.assertEqual(current['available_levels'],['A1','A2'])
        self.assertEqual(len(current['activity_flashcards']),1)
        self.assertTrue(any(v['title']==video['title'] for v in current['videos']))
        self.assertTrue(all(v['level'] in ('A1','A2') for v in current['conversation_catalog']))
        self.assertEqual(self.request('/api/student-level',{'student_id':student['id'],'level':'C2'})[0],403)

    def test_deadline_reminders_and_dictionary(self):
        import deadlines
        self.request('/api/register',{'name':'Tutor','email':'reminder-teacher@example.com','password':'senha-segura123','role':'teacher'})
        mentor=self.cookie;code=self.request('/api/state')[1]['profile']['invite']
        due=(app.now()+app.timedelta(hours=20)).isoformat()
        self.request('/api/activities',{'title':'Entrega con plazo','due_at':due,'instructions':'Responde con frases.','audio':'Hola, tengo una reserva.','tasks':['Comprende','Responde','Continúa'],'resource':''})
        aid=self.request('/api/state')[1]['activities'][0]['id']
        self.register('reminder-student@example.com');self.request('/api/join',{'code':code})
        self.assertEqual(self.request('/api/reminder-preferences',{'channel':'email','email':'reminder-student@example.com'})[0],400)
        self.assertEqual(self.request('/api/reminder-preferences',{'channel':'email','email':'reminder-student@example.com','consent':True})[0],200)
        with patch('deadlines.channels',return_value={'email':True,'whatsapp':False}),patch('deadlines.send') as send:
            deadlines.tick(app.connect,app.now())
            deadlines.tick(app.connect,app.now())
            self.assertEqual(send.call_count,1)
            self.assertEqual(send.call_args.args[0],'email')
            self.assertEqual(self.request('/api/state')[1]['reminder_deliveries'][0]['status'],'accepted')
            self.request('/api/activity-submit',{'activity_id':aid,'answers':['a','b','c']})
            deadlines.tick(app.connect,app.now()+app.timedelta(hours=19))
            self.assertEqual(send.call_count,1,'submitted work must not trigger a second reminder')
        word=self.request('/api/dictionary',{'word':'apellido'})[1]['entry']
        self.assertEqual(word['word'],'apellido')
        self.assertTrue(word['definitions'])
        self.assertEqual(self.request('/api/dictionary',{'letter':'A'})[0],200)
        self.cookie=mentor
        self.assertEqual(self.request('/api/dictionary',{'word':'casa'})[1]['entry']['word'],'casa')

    def test_dictionary_letter_catalog_pagination_and_offline_fallback(self):
        self.register('dictionary-pages@example.com')
        first={'words':['abacería','abacial'],'next_cursor':'page-two'}
        second={'words':['abacista'],'next_cursor':''}
        with patch('dictionary_es.fetch_index',side_effect=[first,second]) as fetch:
            result=self.request('/api/dictionary',{'letter':'A','catalog':True})[1]
            self.assertEqual(result['words'],first['words'])
            self.assertEqual(result['next_cursor'],'page-two')
            self.assertFalse(result['offline'])
            result=self.request('/api/dictionary',{'letter':'A','catalog':True,'cursor':'page-two'})[1]
            self.assertEqual(result['words'],second['words'])
            self.assertEqual(result['next_cursor'],'')
            self.request('/api/dictionary',{'letter':'A','catalog':True})
            self.assertEqual(fetch.call_count,2,'index pages are cached independently')
        with patch('dictionary_es.fetch_index',side_effect=OSError('offline')):
            result=self.request('/api/dictionary',{'letter':'Z','catalog':True})[1]
            self.assertTrue(result['offline'])
            self.assertTrue(any(e['word']=='zapato' for e in result['entries']))

    def test_itinerary_objective_and_written_answers(self):
        self.request('/api/register',{'name':'Tutor','email':'writing-teacher@example.com','password':'senha-segura123','role':'teacher'})
        mentor=self.cookie;code=self.request('/api/state')[1]['profile']['invite']
        self.register('writing-student@example.com');pupil=self.cookie
        self.request('/api/join',{'code':code})
        lessons=self.request('/api/state')[1]['lessons']
        self.assertGreaterEqual(len(lessons),5)
        self.assertTrue(all(l['level']=='A1' for l in lessons))
        self.assertTrue(all(len(l['written_questions'])==2 for l in lessons))
        lesson=next(l for l in app.LESSONS if l['id']=='a1-falsos')
        body={'lesson':lesson['id'],'answers':[q['answer'] for q in lesson['questions']],'written':['Se llama Daniel García y su apodo es Dani.','¿Cuál es su apellido?']}
        result=self.request('/api/submit',body)
        self.assertEqual(result[0],200)
        self.assertNotIn('score',result[1])
        writing=self.request('/api/state')[1]['lesson_writings'][0]
        self.assertEqual(writing['answers'],body['written'])
        self.assertEqual(self.request('/api/submit',{'lesson':'a2-falsos','answers':[0,2,1],'written':['a','b']})[0],403)
        self.cookie=mentor
        received=self.request('/api/state')[1]['students'][0]['lesson_writings'][0]
        self.assertEqual(received['answers'],body['written'])
        self.assertEqual(self.request('/api/lesson-writing-feedback',{'id':writing['id'],'feedback':'Buena distinción entre apellido y apodo.'})[0],200)
        self.cookie=pupil
        self.assertEqual(self.request('/api/state')[1]['lesson_writings'][0]['feedback'],'Buena distinción entre apellido y apodo.')

    def test_dictionary_excludes_other_languages_and_translation_sections(self):
        import dictionary_es
        self.register('spanish-only@example.com')
        with patch('dictionary_es.wiki_api',return_value={'parse':{'sections':[{'line':'Português','index':'1'},{'line':'English','index':'2'}]}}):
            self.assertIsNone(self.request('/api/dictionary',{'word':'soletrar'})[1]['entry'])
        html='<h2>Español</h2><h3>Sustantivo femenino</h3><dl><dd>Definición en español de prueba.</dd></dl><h3>Traducciones</h3><dl><dd>An English translation to exclude.</dd></dl><h2>Português</h2><h3>Substantivo</h3><dl><dd>Definição em português para excluir.</dd></dl>'
        parser=dictionary_es.Definitions();parser.feed(html)
        self.assertEqual(len(parser.entries),1)
        self.assertEqual(parser.entries[0][1],'Definición en español de prueba.')

    def test_twenty_five_lessons_per_level_and_no_personal_names(self):
        from collections import Counter
        import dictionary_es
        counts=Counter(l['level'] for l in app.LESSONS)
        self.assertEqual(dict(counts),{level:25 for level in ('A1','A2','B1','B2','C1','C2')})
        self.assertEqual(len({l['id'] for l in app.LESSONS}),150)
        for lesson in app.LESSONS:
            self.assertGreaterEqual(len(lesson['dialogue']),3)
            self.assertEqual(len(lesson['questions']),3)
            self.assertEqual(len(lesson['written_questions']),2)
            for q in lesson['questions']:
                self.assertEqual(len(q['options']),3)
                self.assertIn(q['answer'],range(3))
        self.assertFalse(dictionary_es.common_word('Ana'))
        self.assertFalse(dictionary_es.common_word('García'))
        self.assertFalse(dictionary_es.common_word('Argentina'))
        self.assertTrue(dictionary_es.common_word('amistad'))
        parser=dictionary_es.Definitions()
        parser.feed('<h2>Español</h2><h3>Nombre propio</h3><dl><dd>Nombre de una persona.</dd></dl><h3>Sustantivo femenino</h3><dl><dd>Definición de una palabra común.</dd></dl>')
        self.assertEqual(len(parser.entries),1)
        self.assertEqual(parser.entries[0][1],'Definición de una palabra común.')

if __name__ == '__main__':
    unittest.main()
