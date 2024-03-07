import dill
import json
from os.path import exists
from datetime import datetime
from groups_logic.Groups import Groups
from aiogram.contrib.fsm_storage.memory import MemoryStorage

class DataBase:
    def __init__(self, admins={}, users={}, dialogues={}, groups=Groups(), users_in_search=[], storage=MemoryStorage(), group_chats={}, dialogues_group={}, users_in_search_group=[], roomchats={}):
        self.admins: dict = admins
        self.users: dict = users
        self.dialogues: dict = dialogues
        self.groups: dict = groups
        self.users_in_search: list = users_in_search
        self.users_in_search_group: list = users_in_search_group
        self.group_chats: dict = group_chats
        self.dialogues_group: dict = dialogues_group
        self.roomchats: dict = roomchats
        self.storage: MemoryStorage = storage
    
    def save_data(self, name_file):
        # Сохранение объекта в файл
        with open(f"data_logic/{name_file}.dill", "wb") as f:
            dill.dump((self.admins, self.users, self.dialogues, self.users_in_search, self.storage), f)

    def open_data(self, name_file):
        # Открытие файла и загрузка объекта
        if exists(f"data_logic/{name_file}.dill"):
            with open(f"data_logic/{name_file}.dill", "rb") as f:
                self.admins, self.users, self.dialogues, self.users_in_search, self.storage = dill.load(f)
                print(self.admins, self.users, self.dialogues, self.users_in_search, self.storage)
    
    def dill_to_json(self, name_file):
        # Загрузка данных из файла, сериализованных с помощью dill
        with open(f'data_logic/{name_file}.dill', 'rb') as file:
            data = dill.load(file)

        # Конвертация данных в JSON и сохранение в файл
        with open(f'data_logic/{name_file}.json', 'w') as file:
            json.dump(data, file, default=lambda o: o.isoformat() if isinstance(o, datetime) else o.__dict__, sort_keys=True, indent=4)