from fasthtml.common import *
import requests
import json

ollama_history = [] 

# @threaded
# def get_response(r, idx):
    


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

    print(f'response: {response}')

    if response.status_code == 200:
        txt = ""
        # Iterate over the streaming response content
        for chunk in response.iter_content(chunk_size=None):  # Adjust chunk_size as needed
            if chunk:
                resp_dict = json.loads(chunk.decode('utf-8'))
                txt += resp_dict['message']['content']
        ollama_history.append({'role' : 'assistant', 'content' : txt})
        return txt
    else:
        return "There is some issue with the solution :("
    
if __name__ == '__main__':
    _ = callOllama("What is artificial intelligence")
    print(_)