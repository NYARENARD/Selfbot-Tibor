
import os

class_vars = {
    "token" : os.getenv("TOKEN"),
    "database" : os.getenv("DATABASE_NAME"),
    "trigger" : os.getenv("TRIGGER_NAME"),
    "channels" : os.getenv("CHANNELS").split(),
    "prefix" : os.getenv("PREFIX"),
    "logchannel" : os.getenv("LOGCHANNEL")
}
