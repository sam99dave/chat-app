"""
TODO:
    - Add response rating to sqlite
"""

from fasthtml.common import *
from fasthtml.oauth import GitHubAppClient
from dotenv import load_dotenv
import os
import requests
import json
import redis
import uuid

from ui_components.home_page import *

load_dotenv()

MODEL_NAME = 'llama3'
redis_ = redis.Redis(host='localhost', port=6379, db=0)
current_chat_name = 'DEFAULT'

# Auth client setup for GitHub
client = GitHubAppClient(os.getenv('GITHUB_OAUTH_CLIENT_ID'), 
                         os.getenv('GITHUB_OAUTH_CLIENT_SECRET'),
                         redirect_uri="http://localhost:8001/auth_redirect")
login_link = client.login_link()

def before(req, session):
    auth = req.scope['auth'] = session.get('user_id', None)
    if not auth: return RedirectResponse('/login', status_code=303)

bware = Beforeware(before, skip=['/login', '/auth_redirect'])

# Set up the app, including daisyui and tailwind for the chat component
tlink = Script(src="https://cdn.tailwindcss.com"),
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
app = FastHTML(before=bware, hdrs=(tlink, dlink, picolink))

# TODO: replace this with a better memory implementation
messages = [] # memory for all the chat for the session!
ollama_history = [] # list of dictionary {'role', 'content'}

@app.get('/logout')
def logout(session):
    session.pop('user_id', None)
    return RedirectResponse('/login', status_code=303)

@app.get('/login')
def login(): #return P(A('Login with GitHub', href=client.login_link()))
    # return Div(
    #     Div(
    #         H2(
    #             "GitHub LogIn!",
    #             cls = 'card-title'
    #         ),
    #         P(
    #             "Log in through GitHub OAuth for access to the chatBot!"
    #         ),
    #         cls = 'card-body',
    #     ),
    #     cls = 'card bg-base-100 w-96 shadow-xl'
    # )
    return Body(
        Div(
            Figure(
                Img(
                    # src = "https://img.daisyui.com/images/stock/photo-1606107557195-0e29a4b5b4aa.webp",
                    src = 'https://img.icons8.com/?size=100&id=K8Hc0huSW4CN&format=png&color=000000',
                    alt = 'tmp_img',
                )
            ),
            Div(
                H2(
                    "GitHub LogIn!",
                    cls = 'card-title'
                ),
                P(
                    "Log in through GitHub OAuth for access to the chatBot!"
                ),
                Div(
                    A('Login with GitHub', href=client.login_link()),
                    cls = 'card-actions justify-end'
                ),
                cls = 'card-body',
            ),
            cls = 'card bg-base-300 w-96 shadow-xl'
        ),
        cls = 'h-screen flex items-center justify-center bg-base-100'
    )

js = """
    function toggleDiv() {
        const div = document.getElementById("main-div");
        // check if the div is currently displayed
        if (div.style.display == "none") {
            // Show the div if its hidden
            div.style.display = "block";
        } else {
            // Hide the div if its shown
            div.style.display = "none";
        }
    }
"""


@app.get('/auth_redirect')
def auth_redirect(code:str, session):
    print(f'code: {code}')
    print(f'session: {session}')
    if not code: return "No code provided!"
    user_id = client.retr_info(code)
    print(f'user_id: {user_id}')
    session['user_id'] = user_id
    print(f'session: {session}')
    return RedirectResponse('/', status_code=303)


# Run the chat model in a separate thread
@threaded
def get_response(r, idx):
    for chunk in r.iter_content(chunk_size=None): 
        print(f'inside chunk!!')
        if chunk:
            resp_dict = json.loads(chunk.decode('utf-8'))
            messages[idx]["content"] += resp_dict['message']['content']

    messages[idx]["generating"] = False

    chat_payload = {"role" : 'assistant', "content" : messages[idx]["content"]}
    ollama_history.append(chat_payload)

    redis_.rpush(current_chat_name, json.dumps(messages[idx - 1])) # user 
    redis_.rpush(current_chat_name, json.dumps(chat_payload)) # assistant

# Route that gets polled while streaming
@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx:int):
    if msg_idx >= len(messages): return ""
    return ChatMessage(msg_idx)

def callOllama(msg):
    url = 'http://localhost:11434/api/chat'
    chat_payload = {"role" : 'user', "content" : msg}
    ollama_history.append(chat_payload)
    payload = {
        'model' : MODEL_NAME,
        'messages' : ollama_history,
        'stream' : True
    }

    response = requests.post(url, json = payload, stream = True)

    if response.status_code == 200:
        return response
    else:
        return None
    
def chatRater(rating_txt: str):
    return A(
        f"{rating_txt}", 
        cls = 'text-green-300' if rating_txt == 'Like' else 'text-red-300', 
        hx_post = '/message-rated', 
        hx_vals = json.dumps({"action" : rating_txt}) # TODO :: some unique id for rating storing
    )

@app.post('/message-rated')
def rate_message(vals: dict):
    """Rate the message and store in DB
    TODO:
        - Indicate that the action has been selected
        - I think this should be done by sending an entirely new chatRater
        - Save this info with appropriate handling to DB (sqlite maybe)"""
    
    return chatRater(vals["action"])
    
def ChatMessage(msg_idx):
    # print(f'messages: {messages}')
    msg = messages[msg_idx]
    txt = msg['content']
    role = msg['role']
    generating = 'generating' in msg and msg['generating']
    chat_class = 'chat-end' if msg['role'] == 'assistant' else 'chat-start'
    print(f'generating: {generating} | chat_class: {chat_class}')
    stream_args = {
        'hx_trigger' : 'every 0.05s',
        'hx_swap' : 'outerHTML', # innerHTML puts this call in infinite loop
        'hx_get' : f'/chat_message/{msg_idx}'
    }
    return Div(
        Div(
            f"{role}",
            cls = 'chat-header'
        ),
        Div(
            f"{txt}",
            cls = 'chat-bubble bg-gray-900',
        ),
        Div(
            chatRater("Like"),
            chatRater("Dislike"),
            cls = 'flex chat-footer opacity-50 space-x-4 p-1'
        ) if role == 'assistant' else Div(),
        cls = f'chat {chat_class}',
        **stream_args if generating else {}

    )

# @app.get('/reset_chat_input')
# def reset_chat_input():
#     return ChatInput()

# The input field for the user message. Also used to clear the
# input field after sending a message via an OOB swap
def ChatInput():
    return Input(type="text", name='msg', id='msg-input',
                 placeholder="Type a message",
                 cls="input input-bordered w-full")
    # return Input(type="text", name='msg', id='msg-input',
    #              placeholder="Type a message",
    #              cls="input input-bordered w-full", hx_swap_oob='true')

@app.post('/new_chat_window')
def get_new_chat_window(vals: dict, session):
    print(f'vals: {vals}')
    # update the message with the current_chat_name db content
    global messages
    messages = []

    global ollama_history
    ollama_history = []

    global current_chat_name
    if 'item_id' in vals:
        current_chat_name = session['user_id']['login'] + '##' + vals['item_id']

    list_length = redis_.llen(current_chat_name)
    for index in range(list_length):
        json_data = redis_.lindex(current_chat_name, index)
        dictionary = json.loads(json_data)
        messages.append(dictionary)
        # print(dictionary)

    ollama_history = messages.copy()
    chat_window = ChatWindow()

    return chat_window

@app.post('/remove_chat_item')
def remove_chat_item(vals: dict, session):
    """Remove chat item from Redis & return empty string as response"""

    dl_key = session['user_id']['login'] + '##' + vals['item_id']
    _ = redis_.delete(dl_key)

    return ""

def newChat(item_name, item_id):
    item_args = {'item_id' : item_id}
    item_tmp = f"{item_name}-{item_id.split('%%')[-1]}"
    chatItem = Li(
        A(
            f"{item_name}",
            id = item_tmp,
            hx_on = 'click',
            hx_post = '/new_chat_window',
            hx_vals = json.dumps(item_args),
            hx_target = '#chatwindow',
            hx_swap = 'outerHTML',
            cls = 'flex-1 text-lg'
        ),
        Button(
            "-",
            cls = 'btn btn-square w-12 h-6',
            style = 'font-size: 1.5rem',
            hx_target = f'#li-{item_tmp}',
            hx_on = 'click',
            hx_post = '/remove_chat_item', # if get or post not specified then the target item is removed by htmx
            hx_vals = json.dumps(item_args),
            hx_swap = 'outerHTML'

        ),
        cls = 'flex flex-row space-x-2',
        id = f'li-{item_tmp}'
    )

    return chatItem

def get_chat_item_names(user_name):
    """Retrieve all the keys(chat items) from Redis"""

    # retreive all the chat item names
    all_keys = redis_.keys('*') 
    all_keys = [key.decode('utf-8') for key in all_keys]
    print(f'allkeys: {all_keys}')
    all_keys = [key for key in all_keys if len(key.split('%%')) == 2 and user_name in key]
    print(f'filteredKeys: {all_keys}')
    all_keys = [key.split('##')[-1] for key in all_keys]
    print(f'ChatfilteredKeys: {all_keys}')

    return all_keys


@app.post('/new_chat')
def get_new_chat(item_name:str):
    print(f'here...')
    # chat_window = ChatWindow()
    key = str(uuid.uuid4())[-6:]
    item_id = f'{item_name}%%{key}'
    new_chat = newChat(item_name, item_id)
    return new_chat

def ChatSideBar(user_name):
    all_keys = get_chat_item_names(user_name)
    sidebar = Div(
        Div(
            Form(
                hx_post = '/new_chat', 
                hx_target = '#chat-history-list',
                hx_swap="beforeend"
            )(
                Input(type="text", name='item_name', placeholder="New Chat Name!!", cls = 'flex-1 rounded-box'),
                Button(
                    "+",
                    cls = 'btn btn-square w-12 h-6',
                    style = 'font-size: 1.5rem',
                    # hx_get = '/new_chat',
                    # hx_target = '#chatwindow',
                    # hx_swap = 'outerHTML',
                    # hx_on = 'submit' # default is this, not reqired but still adding
                ),
                cls = 'flex space-x-2'
            )
        ),
        # Button(
        #     "+",
        #     cls = 'btn btn-square w-12 h-6',
        #     style = 'font-size: 1.5rem',
        #     hx_get = '/new_chat',
        #     hx_target = '#chatwindow',
        #     hx_swap = 'outerHTML',
        #     hx_on = 'submit' # default is this, not reqired but still adding
        # ),
        Div(
            Ul(
                *[newChat(key.split('%%')[0], key) for key in all_keys],
                cls = 'menu menu-vertical bg-base-200 rounded-box h-[500px] overflow-y-auto',
                id = 'chat-history-list'
            ),
            cls = 'flex-1 bg-base-200 p-2 rounded-box'
        ),
        cls = 'flex flex-col space-y-4 w-[300px] p-4 bg-gray-500 text-white rounded',
        id = 'main-div'
    )

    return sidebar


def ChatWindow():
    # TODO :: Button has been disabled as currently of no use!
    toggle_button = Button(
        "Toggle Sidebar",
        Script(js),
        # hx_get = '/toggle_sidebar',
        # hx_target = '#sidebar',
        # hx_swap = 'outerHTML',
        onclick = "toggleDiv()",
        cls = 'btn bg-blue-500 text-white px-4 py-2 rounded mb-4',
        # hx_disable = 'True'
    )
    chatList = Div(
        *[ChatMessage(idx) for idx, msg in enumerate(messages)], 
        id="chatlist", cls="chat-box h-[70vh] overflow-y-auto"
    ),
    page = Form(hx_post='/send_messsage', hx_target="#chatlist", hx_swap="beforeend")(
                # Div(id="chatlist", cls="chat-box h-[70vh] overflow-y-auto"),
                Div(cls="flex space-x-2 mt-2")(
                    Group(
                        ChatInput(), 
                        Button("Send", cls="btn btn-primary")
                    )
                )
           )
    chat_window = Div(
        toggle_button,
        Div(
            chatList, 
            page,
            cls = 'px-16'
        ),
        cls = 'flex-1 p-5 bg-gray-700 text-white rounded',
        id = 'chatwindow'
    )

    # TODO: Toggle can be removed from the chatwindow and kept separate
    return chat_window

@app.get('/chat-window')
def test1(session):
    user_name = session['user_id']['login']
    sidebar = ChatSideBar(user_name)
    chat_window = ChatWindow()
    container = Div(
        sidebar,
        chat_window,
        cls = 'flex w-full max-w px-4 py-2 space-x-4'
    )

    # return Div(chatList, page)

    return container

@app.get('/')
def test():
    navbar = get_navbar()
    main_div = main_template()

    return Body(
        navbar, 
        main_div,
        cls = 'w-[100vw] h-[100vh] overflow-y-hidden'
    )

# @app.get('/')
# def ChatWindow():
#     navbar = get_navbar()
#     chatList = Div(
#         # *[ChatMessage(msg['content']) for msg in messages], 
#         id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"
#     ),
#     page = Form(hx_post='/send_messsage', hx_target="#chatlist", hx_swap="beforeend")(
#                 # Div(id="chatlist", cls="chat-box h-[70vh] overflow-y-auto"),
#                 Div(cls="flex space-x-2 mt-2")(
#                     Group(
#                         ChatInput(), 
#                         Button("Send", cls="btn btn-primary")
#                     )
#                 )
#            )

#     return navbar, chatList, page

@app.post('/send_messsage')
def send(msg:str):
    idx = len(messages)
    messages.append({'role' : 'user', 'content' : msg})
    response = callOllama(msg)
    messages.append({"role":"assistant", "generating":True, "content":""})
    if response:
        print(f'just before chunk!!')
        get_response(response, idx + 1)
    else:
        messages[idx + 1]['generating'] = False

    print(f'just after chunk!!')
    # response = f"sup {msg}" # TODO: replace this with model response

    return ChatMessage(idx), ChatMessage(idx + 1)

    # TODO:: Issue with hx-swap-oob for the Input (Currently Input field won't reset) | SOLVE THIS
    # return ChatMessage(idx), ChatMessage(idx + 1), ChatInput()

# Route that gets polled while streaming
@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx:int):
    if msg_idx >= len(messages): return ""
    return ChatMessage(msg_idx)

if __name__ == '__main__': uvicorn.run("test:app", host='0.0.0.0', port=8001, reload=True)