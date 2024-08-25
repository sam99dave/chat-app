import redis
import json

def main():
    # Connect to Redis server
    r = redis.Redis(host='localhost', port=6379, db=0)

    # # Define chat name and list of dictionaries
    # chat_name = 'chat1'
    # list_of_dicts = [
    #     {'user': 'Alice', 'message': 'Hello!'},
    #     {'user': 'Bob', 'message': 'Hi Alice!'},
    #     {'user': 'Alice', 'message': 'How are you?'}
    # ]

    # # Convert list of dictionaries to JSON
    # list_of_dicts_json = json.dumps(list_of_dicts)

    # # Store the JSON string in Redis with the chat name as the key
    # r.set(chat_name, [])

    # Retrieve and print each dictionary from the Redis list
    list_length = r.llen('DEFAULT')
    for index in range(list_length):
        json_data = r.lindex('DEFAULT', index)
        dictionary = json.loads(json_data)
        print(dictionary)


if __name__ == '__main__':
    main()