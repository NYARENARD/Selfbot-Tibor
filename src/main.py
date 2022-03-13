from config_vars import class_vars
from config_vars import schedule_vars
from bot_class import Bot

import schedule

def msk_to_utc(time_MSK):
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
    instance = Bot(class_vars)

    schedule_flag = schedule_vars["schedule_flag"]
    if schedule_flag:
        launch_time = msk_to_utc(schedule_vars["launch_time"])
        kill_time = msk_to_utc(schedule_vars["kill_time"])
    
        schedule.every().day.at(launch_time).do(instance.genai_enable)
        schedule.every().day.at(kill_time).do(instance.genai_kill)
    
        while True:
            schedule.run_pending()


main()