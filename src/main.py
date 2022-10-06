from config_vars import class_vars
from bot_class import Bot
#from logger_class import Logger

def main():
    instance_bot = Bot(class_vars)
    #instance_logger = Logger(class_vars)
    instance_bot.start()
    #instance_logger.start()

main()
