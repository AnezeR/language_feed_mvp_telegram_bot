class Config:
    def __init__(self):
        import json
        import os
        print(f'{os.path.dirname(__file__)}/config.json')
        config_file = json.load(open(f'{os.path.dirname(__file__)}/config.json'))

        self.telegram_bot_api_key = config_file['telegram_bot_api_key']
        self.admin_chat_id = config_file['admin_chat_id']

        self.current_content = config_file['current_content']
