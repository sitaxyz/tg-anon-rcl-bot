from bot_logic.Bot import Bot
from data_logic.data import DataBase

if __name__ == '__main__':
    

    with open('settings/token.txt', 'r') as f:
        token = f.readline()

    name_file = 'db'
    data = DataBase()
    data.open_data(name_file)
    bot = Bot(token=token, data=data)
    bot.handler_all()
    bot.run()
    data.save_data(name_file)
    data.dill_to_json(name_file)