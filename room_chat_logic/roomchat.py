

class RoomChat:
    def __init__(self, room_id, name, admin_id, capacity, users={}):
        self.room_id: str = room_id
        self.name: str = name
        self.admin_id: int = admin_id
        self.capacity: int = capacity
        self.users: dict = users

    def exit_room(self, user_id):
        pass
    
    def entry_room(self, user_id):
        pass