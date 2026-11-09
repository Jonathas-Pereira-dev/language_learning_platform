"""Prepare invited accounts locally; activation links are private bearer credentials."""
import hashlib
import secrets
from datetime import timedelta
from pathlib import Path
import app


def prepare(teacher_email, student_email):
    app.init_db()
    links = []
    with app.connect() as con:
        con.execute("INSERT OR REPLACE INTO access_settings VALUES('registration_closed','1')")
        teacher_id = None
        for email, role, name in [(teacher_email, 'teacher', 'Docente'), (student_email, 'student', 'Estudiante')]:
            email = email.strip().lower()
            if con.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone():
                raise ValueError('Cuenta existente: no se modifica su contraseña ni su perfil.')
            uid = con.execute('INSERT INTO users(name,email,password,role,invite,teacher_id) VALUES(?,?,?,?,?,?)',
                              (name, email, app.password_hash(secrets.token_urlsafe(48)), role,
                               secrets.token_urlsafe(12) if role == 'teacher' else None, teacher_id)).lastrowid
            if role == 'teacher':
                teacher_id = uid
            token = secrets.token_urlsafe(32)
            con.execute('INSERT INTO resets VALUES(?,?,?)',
                        (hashlib.sha256(token.encode()).hexdigest(), uid,
                         (app.now() + timedelta(days=7)).isoformat()))
            links.append(f'{role}: {email}\n/#reset={token}\n')
    output = app.DB.parent / 'acessos-primeira-senha.txt'
    output.write_text('PRIVADO: entregue somente o link correspondente a cada pessoa.\n'
                      'Substitua / pelo endereço HTTPS do túnel. Validade: 7 dias; uso único.\n\n'
                      + '\n'.join(links), encoding='utf-8')
    print(f'Contas preparadas. Links privados: {output.resolve()}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--teacher', required=True)
    parser.add_argument('--student', required=True)
    args = parser.parse_args()
    prepare(args.teacher, args.student)
