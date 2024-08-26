from fasthtml.common import *
from fasthtml.oauth import GitHubAppClient
import os
from dotenv import load_dotenv

load_dotenv()

# Auth client setup for GitHub
client = GitHubAppClient(os.getenv('GITHUB_OAUTH_CLIENT_ID'), 
                         os.getenv('GITHUB_OAUTH_CLIENT_SECRET'),
                         redirect_uri="http://localhost:8001/auth_redirect")
login_link = client.login_link()

def before(req, session):
    auth = req.scope['auth'] = session.get('user_id', None)
    if not auth: return RedirectResponse('/login', status_code=303)

bware = Beforeware(before, skip=['/login', '/auth_redirect'])

app = FastHTML(before=bware)

@app.get('/')
def home(auth):
    return Div(
        P("Count demo"),
        Button('Increment', hx_get='/increment', hx_target='#count'),
        P(A('Logout', href='/logout'))  # Link to log out,
    )

@app.get('/increment')
def increment(auth):
    return ""

# 37779169
@app.get('/login')
def login(): return P(A('Login with GitHub', href=client.login_link()))

@app.get('/logout')
def logout(session):
    session.pop('user_id', None)
    return RedirectResponse('/login', status_code=303)

@app.get('/auth_redirect')
def auth_redirect(code:str, session):
    print(f'code: {code}')
    print(f'session: {session}')
    if not code: return RedirectResponse('/login', status_code=303)
    user_id = client.retr_info(code)
    print(f'user_id: {user_id}')
    session['user_id'] = user_id
    print(f'session: {session}')
    return RedirectResponse('/', status_code=303)

# serve(port=8000)
if __name__ == '__main__': uvicorn.run("auth:app", host='0.0.0.0', port=8001, reload=True)