import os
import io
import hmac
import pydub
import logging
import hashlib
import requests
import speech_recognition as sr

from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, Blueprint, jsonify, request, current_app

from Client import Client_obj
from openfunctions import make_openai_request
from messages import first_hotel_message, eletronic_message, nutri_message, pizza_message, start_message, limit_message, comercial_extra 

app = Flask(__name__)
webhook_blueprint = Blueprint("webhook", __name__)
load_dotenv()


# OpenAI Assistant IDS
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
AI_CLIENT = OpenAI(api_key=OPEN_AI_API_KEY)

HOTEL_ASSISTANT_ID = os.getenv("HOTEL_ASSISTANT_ID")
LOJA_ELETRONICS_ID = os.getenv("LOJA_ELETRONICS_ID")
NUTRI_ASSISTANT_ID = os.getenv("NUTRICIONISTA_ASSISTANT_ID")
PIZZA_ASSISTANT_ID = os.getenv("PIZZARIA_ASSISTANT_ID")
OPENAI_TEST_MODE = os.getenv("OPENAI_TEST")

# META IDS
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
VERSION = os.getenv("VERSION")

MAX_MESSAGES_PER_PHONE_NUMBER = 50
LANGUAGE = "pt-BR"

# Message log - enable conversation over multiple messages
message_log_dict = dict()
client_obj_list = list()


# handle audio functions

def handle_audio_message(audio_id):
    """Handles audio messages, by accessing the audio from the meta api, downloading it, turning it into text, being the var message that is returned."""
    audio_url = get_media_url(audio_id)
    audio_bytes = download_media_file(audio_url)
    audio_data = convert_audio_bytes(audio_bytes)
    audio_text = recognize_audio(audio_data)
    message = audio_text
    return message

def get_media_url(media_id):
    "Returns media ID/Url"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }
    url = f"https://graph.facebook.com/{VERSION}/{media_id}/"
    response = requests.get(url, headers=headers)
    print(f"media id response: {response.json()}")
    return response.json()["url"]

def download_media_file(media_url):
    "Downloads and returns audio bits"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }
    response = requests.get(media_url, headers=headers)
    print(f"first 10 digits of the media file: {response.content[:10]}")
    return response.content

def convert_audio_bytes(audio_bytes):
    "convert ogg audio bytes to audio data which speechrecognition library can process"
    ogg_audio = pydub.AudioSegment.from_ogg(io.BytesIO(audio_bytes))
    ogg_audio = ogg_audio.set_sample_width(2)  # Set sample width to 2 bytes (16-bit)
    wav_bytes = io.BytesIO()
    ogg_audio.export(wav_bytes, format="wav")
    wav_bytes.seek(0)
    
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(wav_bytes)
    with audio as source:
        audio_data = recognizer.record(source)
    
    return audio_data

def recognize_audio(audio_bytes):
    "run speech recognition on the audio data"
    recognizer = sr.Recognizer()
    audio_text = recognizer.recognize_google(audio_bytes, language=LANGUAGE)
    return audio_text


# Helper functions

def validate_signature(payload, signature):
    " Validate the incoming payload's signature against our expected signature"
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(os.getenv("APP_SECRET"), "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)

def verify():
    """Required webhook verifictaion for WhatsApp from Meta for devs"""
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == VERIFY_TOKEN:
            # Respond with 200 OK and challenge token from the request
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            print("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
        
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        print("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

def update_message_log(message, phone_number, role):
    "create a message log for each phone number and return the current message log"
    initial_log = {
        "role": "system",
        "content": "You are a helpful assistant named WhatsBot.",
    }
    if phone_number not in message_log_dict:
        message_log_dict[phone_number] = [initial_log]
    message_log = {"role": role, "content": message}
    message_log_dict[phone_number].append(message_log)
    return message_log_dict[phone_number]


# Main handle / return functions

def handle_message(): # Main function TODO
    "Main function, that handles an incoming message, contains functionality for maintaing user conection, keeping track of users and messages sent"
    # Parse Request body in json format
    body = request.get_json()
    print(f"request body: {body}")

    try:
        if body.get("object"):
            if (
                body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
                and body["entry"][0]["changes"][0]["value"]["messages"][0]
            ):
                # Verify the signature
                signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
                if not validate_signature(request.data.decode("utf-8"), signature):
                    logging.info("Signature verification failed!")
                    return jsonify({"status": "error", "message": "Invalid signature"}), 403

                # Process the message
                message = body["entry"][0]["changes"][0]["value"]["messages"][0]
                from_number = message["from"]
                message_body = ""
                btn_option_message = ""
                if message["type"] == "text":
                    message_body = message["text"]["body"]
                elif message["type"] == "audio":
                    audio_id = message["audio"]["id"]
                    message_body = handle_audio_message(audio_id)
                elif message["type"] == "button":
                    btn_option_message = message['button']['text']


                obj = Client_obj(from_number, MAX_MESSAGES_PER_PHONE_NUMBER)
    
                #Check first message better
                if from_number not in [str(x) for x in client_obj_list]:
                    first_message = True
                    client_obj_list.append(obj)

                else:
                    first_message = False
                    object_ = [x for x in client_obj_list if str(x) == from_number].pop() #Pulls object out of list
                    object_access = object_.counter_check() # Checks if message limit is hit

                    if object_access == True:
                        pass
                    else: #If its hit, send limit message
                        response = f"{limit_message(MAX_MESSAGES_PER_PHONE_NUMBER)} {comercial_extra}"
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                # Update message log TODO needed?
                message_log = update_message_log(message_body, from_number, "user")

                if first_message == True:
                    send_header(body)
                    return jsonify({"status": "ok"}), 200

                elif first_message == False and object_.type_ == "" and btn_option_message != "":
                    if btn_option_message == "Hotel em Fortaleza":
                        object_.change_type("Hotel em Fortaleza")
                        response = f"{first_hotel_message} {comercial_extra} {start_message}"
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                    elif btn_option_message == "Loja de eletrônicos em SP":
                        object_.change_type("Loja de eletrônicos em SP")
                        response = f"{eletronic_message} {comercial_extra} {start_message}"

                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                    elif btn_option_message == "Nutricionista":
                        object_.change_type("Nutricionista")
                        response = f"{nutri_message} {comercial_extra} {start_message}"

                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200
                    
                    elif btn_option_message == "Pizzaria":
                        object_.change_type("Pizzaria")
                        response = f"{pizza_message} {comercial_extra} {start_message}"

                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                    else:
                        response = "Não entendi! Por favor selecione uma opção valida nos botões acima."
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                elif object_.type_ != "":
                    if str(message_body).strip().lower() == "retornar menu".casefold():
                        object_.change_type("")
                        send_header(body)
                        return jsonify({"status": "ok"}), 200
                    
                    if OPENAI_TEST_MODE == True:
                        object_.counter += 1
                        response = f"The Application is in test mode for OPENAI requests, choosen type: {object_.type_}"
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200
                                
                    elif object_.type_ == "Hotel em Fortaleza":
                        if str(message_body).strip().lower() == "SHOW_DOC".casefold():#TODO AJUST
                            print('reached show_doc')

                            doc_url = "https://drive.google.com/file/d/1zg2e0nKnqkvQnSg85Otop_hE6eoczxRd/view?usp=drive_link"
                            send_document(message["from"], doc_url)
                            return jsonify({"status": "ok"}), 200

                        object_.counter += 1
                        response = make_openai_request(AI_CLIENT, message_body, message["from"], HOTEL_ASSISTANT_ID, message_log_dict)
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                    elif object_.type_ == "Loja de eletrônicos em SP":
                        object_.counter += 1
                        if str(message_body).strip().lower() == "SHOW_DOC".casefold():#TODO AJUST
                            print('reached show_doc')

                            doc_url = "https://drive.google.com/file/d/18M4qH6cVWUFbr1xQIIwVXS26XMPywBs6/view?usp=drive_link"
                            send_document(message["from"], doc_url)
                            return jsonify({"status": "ok"}), 200

                        response = make_openai_request(AI_CLIENT, message_body, message["from"], LOJA_ELETRONICS_ID, message_log_dict)
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                    elif object_.type_ == "Nutricionista":
                        object_.counter += 1
                        if str(message_body).strip().lower() == "SHOW_DOC".casefold():#TODO AJUST
                            print('reached show_doc')

                            doc_url = "https://drive.google.com/file/d/1saWbt2cPzj_zvqEGg9N8WSNd0BrLSfi4/view?usp=drive_link"
                            send_document(message["from"], doc_url)
                            return jsonify({"status": "ok"}), 200
                        
                        response = make_openai_request(AI_CLIENT, message_body, message["from"], NUTRI_ASSISTANT_ID, message_log_dict)
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200
                    
                    elif object_.type_ == "Pizzaria":
                        object_.counter += 1
                        if str(message_body).strip().lower() == "SHOW_DOC".casefold():#TODO AJUST
                            print('reached show_doc')

                            doc_url = "https://drive.google.com/file/d/18WjnyAy9y9vOfXpiEtgjfdR6jd4UB_sb/view?usp=drive_link"
                            send_document(message["from"], doc_url)
                            return jsonify({"status": "ok"}), 200
                        
                        response = make_openai_request(AI_CLIENT, message_body, message["from"], PIZZA_ASSISTANT_ID, message_log_dict)
                        send_whatsapp_message(body, response)
                        return jsonify({"status": "ok"}), 200

                else:
                    response = f'Não entendi! Voce ja selecionou o tipo de assistente! ERRO inesperado'
                    send_whatsapp_message(body, response)
                    return jsonify({"status": "ok"}), 200
                

            return jsonify({"status": "ok"}), 200
        
        else:
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except Exception as e:
        print(f"unknown error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def send_whatsapp_message(body, message):
    "sends whatsapp response / message, given an response message, being the requested var 'message'."
    value = body["entry"][0]["changes"][0]["value"]
    phone_number_id = value["metadata"]["phone_number_id"]
    from_number = value["messages"][0]["from"]
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.facebook.com/{VERSION}/" + phone_number_id + "/messages"
    data = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "text",
        "text": {"body": message},
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"whatsapp message response: {response.json()}")
    response.raise_for_status()

def send_header(body):
    "Sends TEMPLATE header defined in metaAPI, after confirmation that the request is being sent by the first message from a user."
    image_link = "https://imgur.com/RkicXHu.jpg"
    value = body["entry"][0]["changes"][0]["value"]
    phone_number_id = value["metadata"]["phone_number_id"]
    from_number = value["messages"][0]["from"]

    url = f"https://graph.facebook.com/{VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "template",
        "template": {
            "name": "initial_message_options",
            "language": {"code": "pt_BR"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {"link": image_link} 
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"whatsapp message response: {response.json()}")
    response.raise_for_status()

def send_document(from_number, doc_url): #TODO
    """Sends a document message to the given phone number."""
    value = {
        "to": from_number,
        "type": "document",
        "document": {
            "link": doc_url,
            "filename": os.path.basename(doc_url)
        }
    }
    phone_number_id = value["metadata"]["phone_number_id"]

    url = f"https://graph.facebook.com/{VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=value)
    print(f"whatsapp message response: {response.json()}")
    response.raise_for_status()
    

# Main flask functions / webhooks
    
@app.route("/", methods=["GET"])
def home():
    "Sets homepage endpoint and welcome message"
    return "WhatsApp OpenAI Webhook is listening!"


@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    " Accepts both POST and GET requests at /webhook endpoint"
    if request.method == "GET":
        return verify()
    elif request.method == "POST":
        return handle_message()


@app.route("/reset", methods=["GET"])
def reset():
    "Route to reset message log"
    global message_log_dict
    message_log_dict = {}
    return "Message log resetted!"



# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3306)