from fasthtml.common import *
import requests
import json

from ui_components.home_page import *

MODEL_NAME = 'llama3'

# Set up the app, including daisyui and tailwind for the chat component
tlink = Script(src="https://cdn.tailwindcss.com"),
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
app = FastHTML(hdrs=(tlink, dlink, picolink))

# TODO: replace this with a better memory implementation
messages = [] # memory for all the chat for the session!
ollama_history = [] # list of dictionary {'role', 'content'}

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
    
def ChatMessage(msg_idx):
    print(f'messages: {messages}')
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

@app.get('/new_chat_window')
def get_new_chat_window():
    chat_window = ChatWindow()
    return chat_window

def newChat(item_name):
    chatItem = Li(
        A(
            f"{item_name}",
            hx_on = 'click',
            hx_get = '/new_chat_window',
            hx_target = '#chatwindow',
            hx_swap = 'outerHTML',
            cls = 'text-lg'
        )
    )

    return chatItem

@app.post('/new_chat')
def get_new_chat(item_name:str):
    print(f'here...')
    # chat_window = ChatWindow()
    new_chat = newChat(item_name)
    return new_chat

def ChatSideBar():
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
                cls = 'menu menu-vertical bg-base-200 rounded-box h-[500px] overflow-y-auto',
                id = 'chat-history-list'
            ),
            cls = 'flex-1 bg-base-200 p-2 rounded-box'
        ),
        cls = 'flex flex-col space-y-4 w-[300px] p-4 bg-gray-500 text-white rounded',
        style = 'visibility: visible;'
    )

    return sidebar


def ChatWindow():
    # TODO :: Button has been disabled as currently of no use!
    toggle_button = Button(
        "Toggle Sidebar",
        hx_get = '/toggle_sidebar',
        hx_target = '#sidebar',
        hx_swap = 'outerHTML',
        cls = 'btn btn-disabled bg-blue-500 text-white px-4 py-2 rounded mb-4',
        # hx_disable = 'True'
    )
    chatList = Div(
        # *[ChatMessage(msg['content']) for msg in messages], 
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
def test1():
    sidebar = ChatSideBar()
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