from aiogram.dispatcher.filters.state import StatesGroup, State

class UserState(StatesGroup):
    START = State()
    MAIN_MENU = State()
    FINDING = State
    DIALOGUE = State()
    GENDER_REQUEST = State()
    CHANGE_USER_GENDER = State()
    CHANGE_FILTER_GENDER = State()
    SELECT_SIZE_GROUP = State()
    FINDING_GROUP = State()
    DIALOGUE_GROUP = State()
    SELECT_ROOM = State()
    DIALOGUE_ROOM = State()
    CREATE_ROOM_name = State()
    CREATE_ROOM_capacity = State()
    CHANGE_NAME = State()