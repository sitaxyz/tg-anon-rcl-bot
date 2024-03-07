

class GroupChat:
    def __init__(self, num_of_users, list_users, message_count=0):
        self.num_of_users: int = num_of_users
        self.list_users: list = list_users
        self.message_count: int = message_count