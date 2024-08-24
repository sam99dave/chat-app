from fasthtml.common import *
import requests
import json

from ui_components.home_page import *

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
        'model' : 'llama3',
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
            cls = 'chat-bubble'
        ),
        cls = f'chat {chat_class}',
        **stream_args if generating else {}

    )

# The input field for the user message. Also used to clear the
# input field after sending a message via an OOB swap
def ChatInput():
    return Input(type="text", name='msg', id='msg-input',
                 placeholder="Type a message",
                 cls="input input-bordered w-full", hx_swap_oob='true')

# @app.get('/chat-window')
# def test1():
#     chatList = Div(
#         # *[ChatMessage(msg['content']) for msg in messages], 
#         id="chatlist", cls="chat-box h-[70vh] overflow-y-auto"
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

#     return (chatList, page)

# @app.get('/')
# def test():
#     navbar = get_navbar()
#     main_div = main_template()

#     return navbar, main_div

@app.get('/')
def ChatWindow():
    navbar = get_navbar()
    chatList = Div(
        # *[ChatMessage(msg['content']) for msg in messages], 
        id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"
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

    return navbar, chatList, page

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

    return ChatMessage(idx), ChatMessage(idx + 1), ChatInput()

# Route that gets polled while streaming
@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx:int):
    if msg_idx >= len(messages): return ""
    return ChatMessage(msg_idx)

if __name__ == '__main__': uvicorn.run("test:app", host='0.0.0.0', port=8001, reload=True)