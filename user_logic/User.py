from datetime import datetime, timedelta


class User:
    def __init__(self,user_id, chat_id, username, gender=None, group_id=None,
                 interest_filter={}, group_filter={}, gender_filter=[None, 'Мужской', 'Женский'], gender_request=True, date_registration=datetime.now(),
                 dialogue=None, finding=False, dialog_beginning=None, count_messages=0, trying_find=0, num_of_group=None, generate_name='', room_id_select=None, name=None):
        self.user_id: int = user_id
        self.chat_id: int = chat_id
        self.username: str = username
        self.gender: str = gender
        self.group_id: int = group_id
        self.interest_filter: dict = interest_filter
        self.group_filter: dict = group_filter
        self.gender_filter: list = gender_filter
        self.gender_request: bool = gender_request
        self.date_registration: datetime = date_registration
        self.dialogue: bool = dialogue
        self.finding: bool = finding
        self.dialog_beginning: datetime = dialog_beginning
        self.count_messages: int = count_messages
        self.trying_find: int = 0
        self.num_of_group: int = num_of_group
        self.generate_name: str = generate_name
        self.room_id_select: str = room_id_select
        self.name: str = name
    
    @property
    def check_time_for_photo(self):
        return datetime.now() - self.dialog_beginning <= timedelta(minutes=2)
    
    def check_time_for_username(self, text):
        if '@' in text or 't.me' in text:
            return datetime.now() - self.dialog_beginning <= timedelta(minutes=5)
        else:
            return False
    
    def create_time_dialog(self):
        self.dialog_beginning = datetime.now()