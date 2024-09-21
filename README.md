# GenSuite!

![Video Demo](others/output.gif)

- ChatBot
    - [x] ollama setup
    - [x] chat api usage
    - [x] DB implementation for Chat history (For each Chat Item)
    - [x] Chat Item Deletion From DB
    - [x] GitHub OAuth
    - [x] User Based Chat Loading

- UI (FastHTML)
    - [x] Home Page (Basic)
    - [x] Chat Page
        - [x] Horizontal Flex
        - [x] Chat Item
        - [x] Create New Chat Item
        - [x] Delete Existing Chat Item
        - [x] Login page (Decent Page!)
        - [x] SideBar toggle 


## Installation

> Install Poetry

Clone the repo
```bash
git clone https://github.com/sam99dave/chat-app.git
```

Make sure to install `ollama` & `redis-server`. You can start both the services. Ollama mostly will be running by default. Make sure that persistant memory is enabled in redis for retaining the chat history.

```bash
# ollama for linux
curl -fsSL https://ollama.com/install.sh | sh

# start redis server
sudo systemctl start redis-sever

# stop redis server (after stopping the application)
sudo systemctl stop redis-sever
```

Run the application locally!
```bash
# Install the dependencies
cd chat-app
poetry install
poetry shell

# Start the application
cd chatBot
python3 test.py
```

By default its using `llama3` but this can be changed over here:
```Python
# line 19, test.py
# If it works it might take some time as the model will be downloaded
MODEL_NAME = 'llama3'
```

If the above attempt fails then you can download the required model first and then update the `MODEL_NAME` and start the application.

The initial call to the model will take sometime as the model will be loaded in memory!




