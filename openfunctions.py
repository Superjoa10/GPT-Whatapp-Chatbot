import shelve
import time
from openai import OpenAI

# OPENAI API Functions

def make_openai_request(client, message, from_number, assistant_id, message_log_dict): #TODO creating multiple instances
    '''make request to OpenAI'''
    try:
        thread_id = check_if_thread_exists(from_number)
        if thread_id is None:
            print(f"Creating new thread for {from_number}")
            thread = client.beta.threads.create()
            store_thread(from_number, thread.id)
            thread_id = thread.id

        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message,
        )

        assistant = client.beta.assistants.retrieve(assistant_id)

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id,
        )

        # Wait for completion
        while run.status != "completed":
            # Be nice to the API
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        # Retrieve the Messages
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response_message = messages.data[0].content[0].text.value
        print(f"Generated message: {response_message}")

        store_thread(from_number, thread_id)  # Update the thread ID
    except Exception as e:
        print('-------------Exception reached-------------------------------------------------------------------------------------')
        print(f"openai error: {e}")
        response_message = "Sorry, the OpenAI API is currently overloaded or offline. Please try again later."
        remove_last_message_from_log(from_number, message_log_dict)
    return response_message

def remove_last_message_from_log(phone_number, message_log_dict):
    '''remove last message from log if OpenAI request fails'''
    message_log_dict[phone_number].pop()

def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def create_assistant(client):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="hotel_exemple",
        instructions="BE VERY Poligt and explain yourself as a coder named john",
        tools=[{"type": "retrieval"}],
        model="gpt-3.5-turbo-1106",
    )
    return assistant
