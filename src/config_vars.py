
import os

class_vars = {
    "token" : os.getenv("TOKEN"),
    "database" : os.getenv("DATABASE_NAME"),
    "trigger" : os.getenv("TRIGGER_NAME"),
    "channels" : os.getenv("CHANNELS").split(),
    "prefix" : os.getenv("PREFIX"),
    "logchannel" : os.getenv("LOGCHANNEL"),
    "banlist" : os.getenv("BANLIST").split(','),
    "guildID" : os.getenv("GUILDID"),
    "channelID_to_fetch" : os.getenv("CHTOFETCH"),
    "roleID" : os.getenv("ROLEID"),
    "genai_channel" : os.getenv("GENAI_CHANNEL"),
    "shame_channel" : os.getenv("SHAME_CHANNEL")
}

schedule_vars = {
    "schedule_flag" : os.getenv("SCHEDULE_FLAG"),
    "launch_time" : os.getenv("LAUNCH_TIME"),
    "kill_time" : os.getenv("KILL_TIME")
}