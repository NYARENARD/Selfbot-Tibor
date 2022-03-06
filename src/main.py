from config_vars import vars
from Bot_class import Bot

import schedule

def MSK_to_UTC(time_MSK):
    hour = int(time_MSK[0:2]) - 3
    minute = time_MSK[3:5]
    if hour < 0:
        hour += 24
    if hour < 10:
        hour = str('0' + hour)
    else:
        hour = str(hour)
    return hour + ':' + minute

def main():
    token = vars["token"]
    database = vars["database"]
    trigger = vars["trigger"]
    channels = vars["channels"]
    prefix = vars["prefix"]
    logchannel = vars["logchannel"]
    banlist = vars["banlist"]
    guildID = vars["guildID"]
    channelID_to_fetch = vars["channelID_to_fetch"]
    roleID = vars["roleID"]
    schedule_flag = vars["schedule_flag"]
    launch_time = vars["launch_time"]
    kill_time = vars["kill_time"]

    instance = Bot(token, database, trigger, channels, prefix, logchannel, guildID, channelID_to_fetch, roleID, banlist)

    if schedule_flag:
        launch_time = MSK_to_UTC(launch_time)
        kill_time = MSK_to_UTC(kill_time)
    
        schedule.every().day.at(launch_time).do(instance.genai_enable)
        schedule.every().day.at(kill_time).do(instance.genai_kill)
    
        while True:
            schedule.run_pending()


main()