import aiogram
import asyncio
from aiogram import types
from aiogram.types import CallbackQuery, ContentType, ReplyKeyboardRemove
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from .keyboard_logic.build_keyboard import button_builder, inline_button_builder
from data_logic.data import DataBase
from .states.States import UserState
from random import randint, choices
from string import ascii_letters
from user_logic.User import User
from datetime import datetime
from group_chat_logic.GroupChat import GroupChat
from room_chat_logic.roomchat import RoomChat

logging.basicConfig(level=logging.INFO)

class Bot:
    def __init__(self, token, data=DataBase()):
        self.token: str = token
        self.data: DataBase = data
        self.users: dict = self.data.users
        self.admins: dict = self.data.admins
        self.dialogues: dict = self.data.dialogues
        self.users_in_search: list = self.data.users_in_search
        self.users_in_search_group: list = self.data.users_in_search_group
        self.group_chats = self.data.group_chats
        self.dialogues_group: dict = self.data.dialogues_group
        self.groups: Groups = self.data.groups
        self.roomchats: dict = self.data.roomchats
        self.storage: MemoryStorage = self.data.storage
        self.reply_message: dict = {}
        self.init_search_dialogue()

        self.bot: aiogram.Bot = aiogram.Bot(token=self.token)
        self.dp: Dispatcher = Dispatcher(bot=self.bot, storage=self.storage)

    def init_search_dialogue(self):
        self.dialogues_group = {}
        self.dialogues = {}
        self.users_in_search_group = []
        self.users_in_search = []
        for user_id in self.users:
            self.users[user_id].dialogue = False
            self.users[user_id].finding = False
    
    def filter_gender(self, user_id, select_user_id):
        if self.users[user_id].gender in self.users[select_user_id].gender_filter and self.users[select_user_id].gender in self.users[user_id].gender_filter:
            return True
        else:
            return False

    async def search_group_cycle(self, user_id):
        if user_id not in self.users_in_search_group:
            self.users_in_search_group.append(user_id)
        print('group', self.users_in_search_group, datetime.now())
        while not self.users[user_id].dialogue and self.users[user_id].finding and user_id in self.users_in_search_group:
            if len(self.users_in_search_group) >= 3:
                users_in_search_group = self.users_in_search_group[:]
                select_group = []
                for select_user_id in users_in_search_group:
                    if self.users[select_user_id].num_of_group == len(select_group):
                        break
                    if self.users[select_user_id].num_of_group in [None, self.users[user_id].num_of_group]:
                        select_group.append(select_user_id)

                if (not self.users[user_id].num_of_group and len(select_group) >= 3) or len(select_group) == self.users[user_id].num_of_group:
                    print('Группа создана', select_group)
                    group_chat = GroupChat(len(select_group), select_group)
                    for select_id in select_group:
                        self.users[select_id].dialogue = True
                        self.users[select_id].generate_name = ''.join(choices(ascii_letters, k=5))
                        users_group = select_group[:]
                        users_group.remove(select_id)
                        self.dialogues_group[select_id] = users_group
                        self.users_in_search_group.remove(select_id)
                    break
            
            await asyncio.sleep(1)
    
    async def search_cycle(self, user_id):
        if user_id not in self.users_in_search:
            self.users_in_search.append(user_id)
        print(self.users_in_search, datetime.now())

        while not self.users[user_id].dialogue and self.users[user_id].finding and user_id in self.users_in_search:
            if len(self.users_in_search) > 1:
                users_in_search = self.users_in_search[:]
                users_in_search.remove(user_id)
                for select_user_id in users_in_search:
                    if not self.filter_gender(user_id, select_user_id) and self.users[user_id].trying_find < 5:
                        self.users[user_id].trying_find += 1
                        continue
                    self.users[user_id].trying_find = 0

                    self.users[user_id].dialogue = True
                    self.dialogues[user_id] = select_user_id

                    self.users[select_user_id].dialogue = True
                    self.dialogues[select_user_id] = user_id

                    self.reply_message[user_id] = {}
                    self.reply_message[select_user_id] = {}

                    self.users_in_search.remove(user_id)
                    self.users_in_search.remove(select_user_id)
                    break
            await asyncio.sleep(1)
        
    def create_keyboard_rooms(self, page=0):
        rooms = [[{'text': f'{room.name} ({len(room.users)}/{room.capacity})', 'callback_data': f'entry_room---{room.room_id}'}] for room in list(self.roomchats.values())[page*4:(page+1)*4]] if self.roomchats.values() else []
        control = [[{'text': '◀️', 'callback_data': f'select_room---{page-1}'} if page > 0 else [],
                    {'text': 'Создать', 'callback_data': f'create_room'},
                    {'text': '▶️', 'callback_data': f'select_room---{page+1}'} if len(self.roomchats) > (page+1)*4 else []],
                    [{'text': 'Назад', 'callback_data': 'main_menu'}]]

        return inline_button_builder([*rooms, *control])
    
    
    def handler_all(self):


        async def check_verification(message):
            if message.chat.id not in self.users:
                print(f'username {message.from_user.username} chat_id {message.chat.id} user_id {message.chat.id}')
                self.users[message.chat.id] = User(user_id=message.chat.id, chat_id=message.chat.id, username=message.from_user.username)
        
        async def delete_messages(bot: aiogram.Bot, message, count=1):
            for k in range(*((0, count, 1) if count > 0 else (count, 0, -1))):
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-k)
                except:
                    pass


        @self.dp.message_handler(commands=['start'])
        async def start_handler(message: types.Message):
            await check_verification(message)
            keyboard = button_builder([[{'text': 'Меню'}]])
            await message.answer(text='Перейти в меню?', reply_markup=keyboard)

        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'main_menu', state=UserState.SELECT_ROOM)
        async def main_menu_call(call: types.CallbackQuery, state: FSMContext):
            await check_verification(call.message)
            await delete_messages(self.bot, message=call.message)
            await state.finish()
            await main_menu_handler(call.message)

        @self.dp.message_handler(commands=['menu'])
        async def main_menu_handler_commands(message: types.Message):
            await check_verification(message)
            await main_menu_handler(message)
        
        @self.dp.message_handler(text=['Меню', 'Назад в меню'])
        async def main_menu_handler(message: types.Message):
            await check_verification(message)
            keyboard = button_builder([[{'text': '👥Найти собеседника'}, {'text': '👨‍👦‍👦Найти группу'}, {'text': '🚪Комнаты(🆕)'}],
                                       [{'text': '👤Профиль'}]])

            await message.answer(text='🏠Главное меню:', reply_markup=keyboard)


        
        @self.dp.message_handler(text=['🚪Комнаты(🆕)'])
        async def select_room_text(message: types.Message, state: FSMContext):
            await check_verification(message)
            await delete_messages(self.bot, message=message, count=2)
            if not self.users[message.chat.id].name:
                keyboard = button_builder([[{'text': '👤Профиль'}], [{'text': 'Назад в меню'}]])
                await message.answer(text='Нельзя использовать комнаты без имени. Введите свое имя в профиле.', reply_markup=keyboard)
            else:
                
                await state.set_state(state=UserState.SELECT_ROOM)

                keyboard = self.create_keyboard_rooms()

                await message.answer(text='Выберите комнату:', reply_markup=keyboard)
        
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data.split('---')[0] == 'select_room', state=UserState.SELECT_ROOM)
        async def select_room_callback(call: types.CallbackQuery = None, state: FSMContext = None, message: types.Message = None):
            if call:
                message = call.message
                page = int(call.data.split('---')[1])
            else:
                page = 0

            await check_verification(message)
            await delete_messages(self.bot, message=message)
            

            keyboard = self.create_keyboard_rooms(page=page)
            
            await message.answer(text='Выберите комнату:', reply_markup=keyboard)

        @self.dp.callback_query_handler(lambda callback_query: callback_query.data.split('---')[0] == 'entry_room', state=UserState.SELECT_ROOM)
        async def entry_room(call: types.CallbackQuery, state: FSMContext):

            room_id = call.data.split('---')[1]

            self.users[call.message.chat.id].room_id_select = room_id
            self.users[call.message.chat.id].dialogue = True
            self.roomchats[room_id].users[call.message.chat.id] = self.users[call.message.chat.id]
            users_id_in_room = list(self.roomchats[room_id].users.keys())
            users_id_in_room.remove(call.message.chat.id)
            await delete_messages(self.bot, message=call.message)

            await state.set_state(state=UserState.DIALOGUE_ROOM)
            await call.message.answer(text='Вы вошли в комнату.\nИнформация по комнате - /info_room\nВыйти из комнаты - /leave_room')
            for chat_id in users_id_in_room:
                await self.bot.send_message(chat_id=chat_id, text=f'В комнату зашел {self.users[call.message.chat.id].name}.')
        

        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'create_room', state=UserState.SELECT_ROOM)
        async def create_room_name(call: types.CallbackQuery, state: FSMContext):
            await check_verification(call.message)
            await delete_messages(self.bot, message=call.message)

            await state.set_state(state=UserState.CREATE_ROOM_name)

            keyboard = button_builder([[{'text': 'Отменить'}]])
            
            await call.message.answer(text='Введите название комнаты:', reply_markup=keyboard)
        
        @self.dp.message_handler(state=UserState.CREATE_ROOM_name)
        async def create_room_capacity(message: types.Message, state: FSMContext):
            await check_verification(message)
            if message.text == 'Отменить':
                await state.finish()
                await select_room_text(message=message, state=state)
            else:
                await state.set_state(state=UserState.CREATE_ROOM_capacity)
                await state.update_data(data={'name_room': message.text})

                keyboard = button_builder([[{'text': 'Отменить'}]])
                
                await message.answer(text='Введите максимальное количество пользователей в комнате(не больше 32 человек):', reply_markup=keyboard)

        @self.dp.message_handler(state=UserState.CREATE_ROOM_capacity)
        async def create_room_class(message: types.Message, state: FSMContext):
            await check_verification(message)
            if message.text == 'Отменить':
                await state.finish()
                await select_room_text(message=message, state=state)
            elif message.text.isdigit():
                if 1 < int(message.text) <= 32:
                    data = await state.get_data()
                    room_id = ''.join(choices(ascii_letters, k=8))
                    self.users[message.chat.id].room_id_select = room_id
                    self.users[message.chat.id].dialogue = True
                    self.roomchats[room_id] = RoomChat(room_id=room_id, name=data['name_room'], admin_id=message.chat.id,
                                                       capacity=int(message.text), users={message.chat.id: self.users[message.chat.id]})

                    await state.finish()
                    await state.set_state(state=UserState.DIALOGUE_ROOM)
                    await message.answer(text='Вы создали комнату! Сейчас вы находитесь в ней.\nИнформация по комнате - /info_room\nВыйти из комнаты - /leave_room\nУдалить комнату - /delete_room', reply_markup=ReplyKeyboardRemove())
                else:
                    await message.answer(text='Не больше 32 человек.')
                    await select_room_callback(message=message, state=state)
            else:
                await select_room_callback(message=message, state=state)
                
        @self.dp.message_handler(content_types=ContentType.PHOTO, state=UserState.DIALOGUE_ROOM)
        async def message_for_dialogue_with_photos_room(message: types.Message, state: FSMContext = None):
            await check_verification(message)
            photo = message.photo[0].file_id
            await message_for_dialogue_room(message=message, state=state, media=photo)
        
        @self.dp.message_handler(content_types=ContentType.STICKER, state=UserState.DIALOGUE_ROOM)
        async def message_for_dialogue_with_photos_room(message: types.Message, state: FSMContext = None):
            await check_verification(message)
            sticker = message.sticker
            await message_for_dialogue_room(message=message, state=state, sticker=sticker)

        @self.dp.message_handler(content_types=types.ContentType.VOICE, state=UserState.DIALOGUE_ROOM)
        async def for_dialogue_with_voice_room(message: types.Message, state: FSMContext):
            voice_message = message.voice
            await message_for_dialogue_room(message=message, state=state, voice_message=voice_message.file_id)
        
        @self.dp.message_handler(state=UserState.DIALOGUE_ROOM)
        async def message_for_dialogue_room(message: types.Message, state: FSMContext = None, media=None, sticker=None, voice_message=None):
            await check_verification(message)

            if self.users[message.chat.id].room_id_select in self.roomchats and self.users[message.chat.id].room_id_select and self.users[message.chat.id].dialogue:
                users_id_in_room = list(self.roomchats[self.users[message.chat.id].room_id_select].users.keys())
                users_id_in_room.remove(message.chat.id)
                if message.text == '/delete_room' and self.roomchats[self.users[message.chat.id].room_id_select].admin_id == message.chat.id:
                    self.roomchats.pop(self.users[message.chat.id].room_id_select)
                    await message.answer(text='Вы удалили комнату')
                    await state.finish()
                    await select_room_text(message=message, state=state)
                    for chat_id in users_id_in_room:
                        await self.bot.send_message(chat_id=chat_id, text=f'Админ удалил комнату.')
                elif message.text == '/leave_room':
                    await message.answer(text='Вы вышли из комнаты')
                    for chat_id in users_id_in_room:
                        await self.bot.send_message(chat_id=chat_id, text=f'Собеседник {self.users[message.chat.id].name} покинул комнату.')
                    self.roomchats[self.users[message.chat.id].room_id_select].users.pop(message.chat.id, None)
                    self.users[message.chat.id].dialogue = False
                    self.users[message.chat.id].room_id_select = None
                    await state.finish()
                    await select_room_text(message=message, state=state)
                else:
                    self.users[message.chat.id].count_messages += 1
                    if sticker:
                        for chat_id in users_id_in_room:
                            await self.bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)
                            await self.bot.send_message(chat_id=chat_id, text=f'{self.users[message.chat.id].name}: Стикер')
                    elif media:
                        for chat_id in users_id_in_room:
                            await self.bot.send_photo(chat_id=chat_id, photo=media, caption=message.caption)
                    elif voice_message:
                        for chat_id in users_id_in_room:
                            await self.bot.send_voice(chat_id=chat_id, voice=voice_message)
                    else:
                        for chat_id in users_id_in_room: 
                            await self.bot.send_message(chat_id=chat_id, text=f'{self.users[message.chat.id].name}: {message.text}')
            else:
                self.users[message.chat.id].room_id_select = None
                self.users[message.chat.id].dialogue = False
                await state.finish()
                await message.answer(text='Комната удалена')
                await select_room_text(message=message, state=state)


        @self.dp.message_handler(text=['👩‍👨‍👦‍👦Найти группу'])
        async def select_size_group_chat(message: types.Message, state: FSMContext):
            await check_verification(message)
            await state.set_state(state=UserState.SELECT_SIZE_GROUP)

            keyboard = button_builder([[{'text': '3'}, {'text': '4'}, {'text': '5'}, {'text': '6'}, {'text': 'Не важно'}]])
            await message.answer(text='Кол-во людей в группе:', reply_markup=keyboard)
        
        @self.dp.message_handler(text=['3', '4', '5', '6', 'Не важно'], state=UserState.SELECT_SIZE_GROUP)
        async def create_group_chat(message: types.Message, state: FSMContext):
            await check_verification(message)
            if message.text == 'Не важно':
                self.users[message.chat.id].num_of_group = None
            else:
                self.users[message.chat.id].num_of_group = int(message.text)

            await state.set_state(state=UserState.FINDING_GROUP)
            self.users[message.chat.id].finding = True
            self.users[message.chat.id].dialogue = False
            keyboard = button_builder([[{'text': 'Отменить поиск'}]])
            await message.answer(text='Группа подбирается для вас...' , reply_markup=keyboard)
            await self.search_group_cycle(message.chat.id)

            if self.users[message.chat.id].finding:
                self.users[message.chat.id].finding = False
                self.users[message.chat.id].create_time_dialog()
                keyboard = ReplyKeyboardRemove()
                await message.answer(text=f'Группа найдена найдена!\nВаше имя - {self.users[message.chat.id].generate_name}\nКол-во людей - {len(self.dialogues_group[message.chat.id])+1}\nСпустя 2 минуты вы можете отправлять фотографии.\nСпустя 5 минут вы сможете обменяться тг.\nДля отмены диалога напишите /stop.', reply_markup=keyboard)
                await state.set_state(state=UserState.DIALOGUE_GROUP)

        
        @self.dp.message_handler(text=['Отменить поиск'], state=UserState.FINDING_GROUP)
        async def stop_search_group(message: types.Message, state: FSMContext):
            await check_verification(message)
            self.users[message.chat.id].finding = False
            self.users[message.chat.id].dialogue = False
            if message.chat.id in self.users_in_search_group:
                self.users_in_search_group.remove(message.chat.id)
            await state.finish()
            await main_menu_handler(message)
        
        @self.dp.message_handler(state=UserState.DIALOGUE_GROUP)
        async def message_for_dialogue_group(message: types.Message, state: FSMContext = None, media=None, sticker=None):
            await check_verification(message)
            if self.dialogues_group.get(message.chat.id) and self.users[message.chat.id].dialogue:
                if message.text == '/stop':
                    await message.answer(text='Вы отключились от группы' )
                    for chat_id in self.dialogues_group[message.chat.id]:
                        await self.bot.send_message(chat_id=chat_id, text=f'Собеседник {self.users[message.chat.id].generate_name} отключился')
                        self.dialogues_group[chat_id].remove(message.chat.id)

                    self.users[message.chat.id].dialogue = False
                    self.dialogues_group[message.chat.id] = None

                    keyboard = inline_button_builder([[{'text': 'Поиск', 'callback_data': 'new_search_group'}, {'text': 'Главное Меню', 'callback_data': 'main_menu_group'}]])
                    await message.answer(text='Выберите действие:', reply_markup=keyboard)
                else:
                    self.users[message.chat.id].count_messages += 1
                    if sticker:
                        for chat_id in self.dialogues_group[message.chat.id]:
                            await self.bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)
                    elif media:
                        if self.users[message.chat.id].check_time_for_photo:
                            await message.answer(text='❌Вы пока не можете отправлять фотографии')
                        else:
                            for chat_id in self.dialogues_group[message.chat.id]:
                                await self.bot.send_photo(chat_id=chat_id, photo=media, caption=message.caption)
                    else:
                        if self.users[message.chat.id].check_time_for_username(message.text):
                            await message.answer(text='❌Вы пока не можете отправлять ссылки или свой тг')
                        else:
                            for chat_id in self.dialogues_group[message.chat.id]: 
                                await self.bot.send_message(chat_id=chat_id, text=f'{self.users[message.chat.id].generate_name}: {message.text}')
            elif not self.users[message.chat.id].finding:
                keyboard = inline_button_builder([[{'text': 'Поиск', 'callback_data': 'new_search_group'}, {'text': 'Главное Меню', 'callback_data': 'main_menu_group'}]])
                await message.answer(text='Выберите действие:', reply_markup=keyboard)
            else:
                self.users[message.chat.id].dialogue = False
                self.users[message.chat.id].finding = False
        
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'main_menu_group', state=UserState.DIALOGUE_GROUP)
        async def main_menu_from_groupchat(call: types.CallbackQuery = None, state: FSMContext = None):
            await check_verification(call.message)
            await delete_messages(self.bot, call.message)
            await state.finish()
            await main_menu_handler(call.message)
        
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'new_search_group', state=UserState.DIALOGUE_GROUP)
        async def main_menu_from_groupchat(call: types.CallbackQuery = None, state: FSMContext = None):
            await check_verification(call.message)
            await delete_messages(self.bot, call.message)
            await state.finish()
            await select_size_group_chat(call.message, state)
            

        @self.dp.message_handler(text=['👤Профиль', 'Профиль'])
        async def main_settings(message: types.Message):
            await check_verification(message)
            gender_request = 'Отключить' if self.users[message.chat.id].gender_request else 'Включить'
            keyboard = button_builder([[{'text': 'Сменить пол'}, {'text': 'Пол собеседника'}, {'text': 'Сменить имя'}],
                                       [{'text': f'Запрос пола собеседника ({gender_request})'}],
                                       [{'text': 'Назад в меню'}]])
            gender = self.users[message.chat.id].gender if self.users[message.chat.id].gender else 'Не указан'
            gender_request = 'Запрашивать' if self.users[message.chat.id].gender_request else 'Пропускать'
            gender_companion = self.users[message.chat.id].gender_filter[0] if self.users[message.chat.id].gender_filter in [['Мужской'], ['Женский']] else 'Не указан'
            name = self.users[message.chat.id].name if self.users[message.chat.id].name else 'Не указано'
            await message.answer(text=f'🌟 Профиль:\n Имя - {name}\n Пол - {gender}\n Пол собеседника - {gender_companion}\n Запрос пола - {gender_request}', reply_markup=keyboard)
        
        @self.dp.message_handler(text=['Сменить имя'])
        async def change_name(message: types.Message, state: FSMContext):
            await check_verification(message)
            await state.set_state(state=UserState.CHANGE_NAME)
            keyboard = button_builder([[{'text': 'Отменить'}]])
            await message.answer(text='Введите новое имя:', reply_markup=keyboard)

        @self.dp.message_handler(state=UserState.CHANGE_NAME)
        async def change_name_select(message: types.Message, state: FSMContext):
            await check_verification(message)
            if message.text == 'Отменить':
                await state.finish()
                await main_settings(message=message)
            elif message.text not in [user.name for user in self.users.values()]:
                await state.finish()
                self.users[message.chat.id].name = message.text
                await main_settings(message=message)
            else:
                await message.answer(text='Имя занято, введите другое.')
                await change_name(message=message, state=state)

        
        @self.dp.message_handler(text=['Запрос пола собеседника (Отключить)', 'Запрос пола собеседника (Включить)'])
        async def searching_users_select(message: types.Message):
            await check_verification(message)
            self.users[message.chat.id].gender_request = not self.users[message.chat.id].gender_request
            await main_settings(message)
        
        @self.dp.message_handler(text=['Пол собеседника'])
        async def change_gender(message: types.Message, state: FSMContext):
            await check_verification(message)
            await state.set_state(state=UserState.CHANGE_FILTER_GENDER)
            keyboard = button_builder([[{'text': 'Мужской'}, {'text': 'Женский'}, {'text': 'Не важно'}]])
            await message.answer(text=f'Выберите пол собеседника:', reply_markup=keyboard)
        
        @self.dp.message_handler(text=['Мужской', 'Женский', 'Не важно'], state=UserState.CHANGE_FILTER_GENDER)
        async def change_gender(message: types.Message, state: FSMContext):
            await check_verification(message)
            if 'Мужской' == message.text:
                self.users[message.chat.id].gender_filter = ['Мужской']
            elif 'Женский' == message.text:
                self.users[message.chat.id].gender_filter = ['Женский']
            else:
                self.users[message.chat.id].gender_filter = [None, 'Мужской', 'Женский']
            await state.finish()
            await main_settings(message)

        @self.dp.message_handler(text=['Сменить пол'])
        async def change_gender(message: types.Message, state: FSMContext):
            await state.set_state(state=UserState.CHANGE_USER_GENDER)
            keyboard = button_builder([[{'text': 'Мужской'}, {'text': 'Женский'}, {'text': 'Не указывать'}]])
            await message.answer(text=f'Выберите свой пол:', reply_markup=keyboard)
            
        @self.dp.message_handler(text=['Мужской', 'Женский', 'Не указывать'], state=UserState.CHANGE_USER_GENDER)
        async def change_gender(message: types.Message, state: FSMContext):
            if message.text == 'Не указывать':
                self.users[message.chat.id].gender = None
            elif message.text == 'Мужской':
                self.users[message.chat.id].gender = 'Мужской'
            else:
                self.users[message.chat.id].gender = 'Женский'
            await state.finish()
            await main_settings(message)

        @self.dp.message_handler(text=['👥Найти собеседника'])
        async def searching_users_select(message: types.Message, state: FSMContext):
            await check_verification(message)
            if not self.users[message.chat.id].gender_request:
                await state.set_state(state=UserState.DIALOGUE)
                await searching_users_without_gender(message, state)
            else:
                await state.set_state(state=UserState.GENDER_REQUEST)
                keyboard = button_builder([[{'text': 'Муж.'}, {'text': 'Жен.'}, {'text': 'Не важно'}]])
                await message.answer(text='Выберите пол:', reply_markup=keyboard)
        
        @self.dp.message_handler(text=['Муж.', 'Жен.', 'Не важно'], state=UserState.GENDER_REQUEST)
        async def gender_select(message: types.Message, state: FSMContext):
            if 'Муж.' == message.text:
                self.users[message.chat.id].gender_filter = ['Мужской']
            elif 'Жен.' == message.text:
                self.users[message.chat.id].gender_filter = ['Женский']
            else:
                self.users[message.chat.id].gender_filter = [None, 'Мужской', 'Женский']

            await state.set_state(state=UserState.DIALOGUE)
            await searching_users(message, state)
        
        @self.dp.message_handler(text=['Убрать фильтры'], state=UserState.DIALOGUE)
        async def searching_users_without_gender(message: types.Message, state: FSMContext):
            self.users[message.chat.id].gender_filter = [None, 'Мужской', 'Женский']
            keyboard = button_builder([[{'text': 'Отменить поиск'}]])
            await message.answer(text='Фильтры убраны', reply_markup=keyboard)
        
        @self.dp.message_handler(text=[], state=UserState.DIALOGUE)
        async def searching_users(message: types.Message, state: FSMContext):
            await check_verification(message)
            self.users[message.chat.id].finding = True
            self.users[message.chat.id].dialogue = False
            if not self.users[message.chat.id].gender_filter == [None, 'Мужской', 'Женский']:
                keyboard = button_builder([[{'text': 'Отменить поиск'}], [{'text': 'Убрать фильтры'}]])
            else:
                keyboard = button_builder([[{'text': 'Отменить поиск'}]])

            await message.answer(text='Собеседник подбирается для вас...' , reply_markup=keyboard)
            await state.set_state(state=UserState.DIALOGUE)
            await self.search_cycle(message.chat.id)

            if self.users[message.chat.id].finding:
                self.users[message.chat.id].finding = False
                self.users[message.chat.id].create_time_dialog()
                keyboard = ReplyKeyboardRemove()
                await message.answer(text='Собеседник найден!\nСпустя 2 минуты вы можете отправлять фотографии.\nСпустя 5 минут вы сможете обменяться тг.\nДля отмены диалога напишите /stop.' , reply_markup=keyboard)
                await state.set_state(state=UserState.DIALOGUE)

        @self.dp.message_handler(text=['Отменить поиск'], state=UserState.DIALOGUE)
        async def cancel_finding(message: types.Message, state: FSMContext):
            await check_verification(message)
            self.users[message.chat.id].finding = False
            if message.chat.id in self.users_in_search:
                self.users_in_search.remove(message.chat.id)
            await state.finish()
            await main_menu_handler(message)
        
        @self.dp.message_handler(content_types=ContentType.PHOTO, state=UserState.DIALOGUE)
        async def message_for_dialogue_with_photos(message: types.Message, state: FSMContext = None):
            await check_verification(message)
            photo = message.photo[0].file_id
            await message_for_dialogue(message=message, state=state, media=photo)
        
        @self.dp.message_handler(content_types=ContentType.STICKER, state=UserState.DIALOGUE)
        async def message_for_dialogue_with_photos(message: types.Message, state: FSMContext = None):
            await check_verification(message)
            sticker = message.sticker
            await message_for_dialogue(message=message, state=state, sticker=sticker)

        @self.dp.message_handler(content_types=types.ContentType.VOICE, state=UserState.DIALOGUE)
        async def for_dialogue_with_voice(message: types.Message, state: FSMContext):
            voice_message = message.voice
            await message_for_dialogue(message=message, state=state, voice_message=voice_message.file_id)

        @self.dp.message_handler(state=UserState.DIALOGUE)
        async def message_for_dialogue(message: types.Message, state: FSMContext = None, media=None, sticker=None, voice_message=None):
            await check_verification(message)
            if self.dialogues.get(message.chat.id) and self.users[message.chat.id].dialogue:
                if message.text == '/stop':
                    await message.answer(text='Вы отключились от собеседника' )

                    await self.bot.send_message(chat_id=self.dialogues[message.chat.id], text='Собеседник отключился' )

                    keyboard = inline_button_builder([[{'text': 'Поиск', 'callback_data': 'new_search'}, {'text': 'Главное Меню', 'callback_data': 'main_menu'}]])
                    await message.answer(text='Выберите действие:', reply_markup=keyboard)
                    await self.bot.send_message(chat_id=self.dialogues[message.chat.id], text='Выберите действие:', reply_markup=keyboard)
                    self.users[self.dialogues[message.chat.id]].dialogue = False
                    self.users[message.chat.id].dialogue = False
                    self.dialogues[self.dialogues[message.chat.id]] = None
                    self.dialogues[message.chat.id] = None

                else:
                    self.users[message.chat.id].count_messages += 1
                    if sticker:
                        reply_msg = None
                        if message.reply_to_message:
                            reply_msg = self.reply_message[message.chat.id][message.reply_to_message.message_id]

                        message_send = await self.bot.send_sticker(chat_id=self.dialogues[message.chat.id], sticker=sticker.file_id)

                        self.reply_message[message.chat.id][message.message_id] = message_send.message_id
                        self.reply_message[self.dialogues[message.chat.id]][message_send.message_id] = message.message_id
                    elif media:
                        if self.users[message.chat.id].check_time_for_photo:
                            await message.answer(text='❌Вы пока не можете отправлять фотографии')
                        else:
                            reply_msg = None
                            if message.reply_to_message:
                                reply_msg = self.reply_message[message.chat.id][message.reply_to_message.message_id]

                            message_send = await self.bot.send_photo(chat_id=self.dialogues[message.chat.id], photo=media, caption=message.caption)

                            self.reply_message[message.chat.id][message.message_id] = message_send.message_id
                            self.reply_message[self.dialogues[message.chat.id]][message_send.message_id] = message.message_id   
                    elif voice_message:
                        reply_msg = None
                        if message.reply_to_message:
                            reply_msg = self.reply_message[message.chat.id][message.reply_to_message.message_id]

                        message_send = await self.bot.send_voice(chat_id=self.dialogues[message.chat.id], voice=voice_message)

                        self.reply_message[message.chat.id][message.message_id] = message_send.message_id
                        self.reply_message[self.dialogues[message.chat.id]][message_send.message_id] = message.message_id
                    else:
                        if self.users[message.chat.id].check_time_for_username(message.text):
                            await message.answer(text='❌Вы пока не можете отправлять ссылки или свой тг')
                        else:
                            reply_msg = None
                            if message.reply_to_message:
                                reply_msg = self.reply_message[message.chat.id][message.reply_to_message.message_id]

                            message_send = await self.bot.send_message(chat_id=self.dialogues[message.chat.id], reply_to_message_id=reply_msg, text=message.text)

                            self.reply_message[message.chat.id][message.message_id] = message_send.message_id
                            self.reply_message[self.dialogues[message.chat.id]][message_send.message_id] = message.message_id
            elif not self.users[message.chat.id].finding:
                keyboard = inline_button_builder([[{'text': 'Поиск', 'callback_data': 'new_search'}, {'text': 'Меню', 'callback_data': 'main_menu'}]])
                await message.answer(text='Выберите действие:', reply_markup=keyboard)
            else:
                self.users[message.chat.id].dialogue = False
                self.users[message.chat.id].finding = False
            
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'main_menu', state=UserState.DIALOGUE)
        async def from_dialog_in_menu(call: types.CallbackQuery = None, state: FSMContext = None):
            await check_verification(call.message)
            await delete_messages(self.bot, call.message)
            await state.finish()
            await main_menu_handler(call.message)
        
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data == 'new_search', state=UserState.DIALOGUE)
        async def from_dialog_in_dialog(call: types.CallbackQuery = None, state: FSMContext = None):
            await check_verification(call.message)
            await delete_messages(self.bot, call.message)
            await state.finish()
            await searching_users_select(call.message, state)
        
        @self.dp.message_handler(commands=['all_info_users'])
        async def all_count_users_handler(message: types.Message):
            await check_verification(message)
            if self.users[message.chat.id].username == 'sitaxyzxc':
                s = ''
                count_finding = 0
                count_dialogue = 0
                count_messages = 0
                for user in self.users.values():
                    if user.finding:
                        count_finding += 1
                    elif user.dialogue:
                        count_dialogue += 1
                    count_messages += user.count_messages
                    s += (f'\n{user.user_id}: @{user.username}, 🔍 - {"✅" if user.finding else "❌"}, ✉️ - {"✅" if user.dialogue else "❌"}')

                texts = f'👥 Количество людей - {len(self.users)}\n🔵 В cети - {count_dialogue+count_finding}\n💬 В диалоге - {count_dialogue}\n🔍 В поиске - {count_finding}\n✉️ Всего сообщений написано - {count_messages}'
                texts += f'\n\nИнформация по каждому пользователю:\n{s}'
                texts = [texts[i:i + 1000] for i in range(0, len(texts), 1000)]
                keyboard = inline_button_builder([[{'text': 'Сбросить диалоги', 'callback_data': f'reset_dialogues---{len(texts)}'}], [{'text': 'Обновить данные', 'callback_data': f'reload_info_users---{len(texts)}'}]])
                for i in texts[:-1]:
                    await message.answer(text=i)
                await message.answer(text=texts[-1], reply_markup=keyboard)
            
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data.split('---')[0] == 'reset_dialogues')
        async def reset_dialogues(call: types.CallbackQuery = None, state: FSMContext = None):
            k = int(call.data.split('---')[1])
            for user_id in self.users:
                if self.users[user_id].dialogue:
                    self.users[user_id].dialogue = False
                    await self.bot.send_message(chat_id=user_id, text='Ваш диалог был прерван по тех. причинам.' )
                    await message_for_dialogue(call.message)
            self.dialogues = {}
            await delete_messages(self.bot, call.message, k)
            await all_count_users_handler(call.message)
        
        @self.dp.callback_query_handler(lambda callback_query: callback_query.data.split('---')[0] == 'reload_info_users')
        async def reset_dialogues(call: types.CallbackQuery = None, state: FSMContext = None):
            k = int(call.data.split('---')[1])
            await delete_messages(self.bot, call.message, k)
            await all_count_users_handler(call.message)

        
        @self.dp.message_handler(commands=['info_users'])
        async def count_users_handler(message: types.Message):
            await check_verification(message)
            if self.users[message.chat.id].username == 'sitaxyzxc':
                s = ''
                count_finding = 0
                count_dialogue = 0
                count_messages = 0
                for user in self.users.values():
                    if user.finding:
                        count_finding += 1
                    elif user.dialogue:
                        count_dialogue += 1
                    count_messages += user.count_messages

                texts = f'Количество людей - {len(self.users)}\nВ cети - {count_dialogue+count_finding}\nВ диалоге - {count_dialogue}\nВ поиске - {count_finding}\nВсего сообщений написано - {count_messages}'
                texts = [texts[i:i + 1000] for i in range(0, len(texts), 1000)]
                for i in texts:
                    await message.answer(text=i)
        
        @self.dp.message_handler(commands=['message_for_users'])
        async def count_users_handler(message: types.Message):
            await check_verification(message)
            if self.users[message.chat.id].username == 'sitaxyzxc':
                users = list(self.users.keys())
                for chat_id in users:
                    if self.users[chat_id] != 'sitaxyzxc':
                        try:
                            await self.bot.send_message(chat_id=chat_id, text=f'Уведомление от админа: {message.text[18:]}')
                        except:
                            print(f'Пользователь {chat_id} забанил бота')
                            self.users.pop(chat_id)

        @self.dp.message_handler(commands=['stop_bot'])
        async def stop_bot(message: types.Message):
            await check_verification(message)
            if self.users[message.chat.id].username == 'sitaxyzxc':
                self.dp.stop_polling()
                await self.dp.wait_closed()
                exit
        
        @self.dp.message_handler(commands=['save_to_json'])
        async def save_to_json(message: types.Message):
            await check_verification(message)
            if self.users[message.chat.id].username == 'sitaxyzxc':
                self.data.dill_to_json('db')
                await message.answer(text='Вы сохранили DB в json файл.')

        @self.dp.message_handler()
        async def no_feedback(message: types.Message):
            await check_verification(message)
            print('Новое сообщение вне команд')
            await message.answer(text='👾: Я не понимаю вас.')
    


    def run(self):
        executor.start_polling(self.dp, skip_updates=True)