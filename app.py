
import logging
import threading  # TEST


from flask import Flask, render_template, request
from flask_socketio  import SocketIO, emit

from partygpt import AiGuest
from partygpt.humanly import Persona
from partygpt.comms.various import read_yaml


PATH_SETTINGS = 'settings.yml'
APPLICATION_SETTINGS = read_yaml(path=PATH_SETTINGS)['application']
PATH_FOLDER_CONVERSATION_RECORDS = APPLICATION_SETTINGS['conversation_records_folder']
REFRESH_TIMER_AI_GOODBYE = APPLICATION_SETTINGS['refresh_conversation_after_ai_says_goodbye']

app = Flask(__name__)
# app.config['SERVER_NAME'] = '127.0.0.1:5000'
app.config['SECRET_KEY'] = 'party_gpt1213!'
# https://flask-socketio.readthedocs.io
sockets = SocketIO(app)


log_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.INFO)
log_console_handler.setFormatter(log_formatter)
log_file_handler = logging.FileHandler('debug.log', encoding='utf-8')
log_file_handler.setLevel(logging.DEBUG)
log_file_handler.setFormatter(log_formatter)
root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.setLevel(level=logging.DEBUG)
root_logger.addHandler(log_file_handler)
root_logger.addHandler(log_console_handler)

logger = logging.getLogger(__name__)


@sockets.on('connection')
def log_connect(data):
    if data['state'] == 'success':
        logger.info('Client connected successfully.')

@app.route('/')
def index():
    ai_guest.set_conversation_record_folder_path(PATH_FOLDER_CONVERSATION_RECORDS)
    return render_template('index.html')

@app.route('/process-input', methods=['POST'])
def process_input():
    data = request.get_json()
    message = data['message']
    if message:
        tmp_message_log = message.replace('\r', '\\r').replace('\n', '\\n')
        logger.info(f'User Message: {tmp_message_log}')
    response = ai_guest.communicate(user_input=message)
    # TEST
    # response = 'an AI response'
    # TEST
    if response:
        tmp_response_log = response.replace('\r', '\\r').replace('\n', '\\n')
        logger.info(f'AI response: {tmp_response_log}')

    logger.info(f'Current costs: {ai_guest.get_accumulated_costs(verbose=False)}')
    logger.info(f'Current length of message history: {ai_guest.count_messages()}')  # TODO: debug
    return {'reply': response}

@app.route('/save-records', methods=['GET'])
def save_records():
    ai_guest.save_messages_history()
    return '', 200

@app.route('/close-session', methods=['GET'])
def refresh_session():
    logger.info('Session refreshed (per frontend).')
    ai_guest.reset(persona=None)
    return ''  # may not return None or omit return statement

def trigger_session_refresh(goodbye_msg):
    logger.info('Session refreshed (per backend).')
    sockets.emit('instruction', {
        'type': 'refresh_session_timer',
        'timer': REFRESH_TIMER_AI_GOODBYE,
        'goodbye_msg': goodbye_msg})  # TODO: if more clients, seesion ID needs to be used


if __name__ == '__main__':
    logger.info('System starting.')
    if PATH_FOLDER_CONVERSATION_RECORDS:
        logger.info(f'Conversations will be recorded to folder {PATH_FOLDER_CONVERSATION_RECORDS}.')
    else:
        logger.info(f'Conversations will not be recorded.')

    def end_communication(goodbye: str):
        trigger_session_refresh(goodbye_msg=goodbye)
        return

    # persona = Persona(character='smarty-pants',
    #         profession='rocket scientist',
    #         experience='been a blast in a science slam',
    #         aspiration='you want to set a new world record',
    #         special_skill='start playing a quiz on basic knowledge with the guest')
    ai_guest = AiGuest(
        path_settings=PATH_SETTINGS,
        persona=None,
        functions=[end_communication],
        conversation_record_folder_path=PATH_FOLDER_CONVERSATION_RECORDS)

    # # TEST
    # thread = threading.Thread(target=trigger_session_refresh)
    # thread.start()
    # # TEST

    sockets.run(app=app)
