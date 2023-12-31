import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import datetime
from core import VkTools
from config import group_token, access_token

from data_store import check_user, add_user, engine


class BotInterface():
    def __init__(self, group_token, access_token):
        self.vk = vk_api.VkApi(token=group_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.worksheets = []
        self.keys = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def photos_for_send(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photo_string

    def new_message(self, k):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if k == 0:
                    if any(char.isdigit() for char in event_text):
                        self.message_send(event.user_id, 'Пожалуйста, введите имя и фамилию:')
                    else:
                        return event_text

                if k == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.message_send(event.user_id, 'Некорректно введен формат пола. Введите 1 или 2:')

                if k == 2:
                    if any(char.isdigit() for char in event_text):
                        self.message_send(event.user_id, 'Город не найден. ВВедите название города без чисел:')
                    else:
                        return event_text

                if k == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.message_send(event.user_id, 'Пожалуйста, введите дату вашего рождения (дд.мм.гггг):')
                    else:
                        return self._bdate_toyear(event.text)

    def send_msg_exc(self, event):
        if self.params['name'] is None:
            self.message_send(event.user_id, 'Введите ваше имя и фамилию:')
            return self.new_message(0)

        if self.params['sex'] is None:
            self.message_send(event.user_id, 'Введите свой пол (1-м, 2-ж):')
            return self.new_message(1)

        elif self.params['city'] is None:
            self.message_send(event.user_id, 'Введите ваш город:')
            return self.new_message(2)

        elif self.params['year'] is None:
            self.message_send(event.user_id, 'Введите дату вашего рождения (дд.мм.гггг):')
            return self.new_message(3)

    def process_worksheet(self, engine, user_id, worksheet):
        if not check_user(engine, user_id, worksheet['id']):
            add_user(engine, user_id, worksheet['id'])
            return worksheet
        return None

    def get_profile(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()
                result = self.process_worksheet(engine, event.user_id, worksheet)
                if result is not None:
                    yield result
            else:
                worksheets = self.vk_tools.search_worksheet(self.params, self.offset)


    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                text = event.text.lower()
                if text == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Приветствую тебя, {self.params["name"]}')
                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            self.params[i] = self.send_msg_exc(event)
                    self.message_send(event.user_id, 'Вы зарегистрированны!')

                elif text == 'поиск':
                    self.message_send(event.user_id, 'Ищу пару...')
                    msg = next(iter(self.get_profile(self.worksheets, event)))
                    if msg:
                        photo_string = self.photos_for_send(msg)
                        self.offset += 10
                        self.message_send(event.user_id, f'имя: {msg["name"]} ссылка: vk.com/id{msg["id"]}', attachment=photo_string)

                elif text.lower() == 'пока':
                    self.message_send(event.user_id, 'Пока - пока, заходи еще')
                else:
                    self.message_send(event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(group_token, access_token)
    bot_interface.event_handler()
