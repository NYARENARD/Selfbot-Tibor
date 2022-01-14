import discum
import time
import random
import schedule
import os
from threading import Thread

class Bot:
    
    global bot

    token = os.getenv("TOKEN")
    database = os.getenv("DATABASE_NAME")
    trigger = os.getenv("TRIGGER_NAME")
    allowed_channels = os.getenv("ALLOWED_CHANNELS").split()


    def __init__(self):
        self.bot = discum.Client(token=self.token, log=False)
        print("\n>>> Подключение успешно.\n")
        self.enable_genai()
		
	#команды включения и отключения бота Genai в определенном канале		
    def enable_genai(self):
        self.bot.sendMessage("730552031735054337", "g.interval random")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen +")
	
    def kill_genai(self):
        self.bot.sendMessage("730552031735054337", "g.interval off")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen -")


    def is_triggered(self, content):
        with open(self.trigger, 'r', encoding="utf-8") as f:
            for line in f:
                if line.strip() in content.lower():
                    return True
            return False  

    def response(self, channelID):
        time.sleep(random.randint(7, 15))
        self.bot.typingAction(channelID)
        with open(self.database, 'r', encoding="utf-8") as f:
            base_ar = f.read().split('\n')
            return random.choice(base_ar)

    def timestamp_parse(self, raw):
        sec = raw[17:22]
        minu = raw[14:16]
        hr = int(raw[11:13]) + 3
        day = str(int(raw[8:10]) + hr // 24)
        hr = str(hr % 24)
        mon = raw[5:7]
        year = raw[0:4]
        timestamp = hr+':'+minu+':'+sec+' '+day+'-'+mon+'-'+year
        return timestamp

    def main_launch(self):

        global bot

        @self.bot.gateway.command
        def reaction_add(resp):
            if resp.event.reaction_added:
                m = resp.parsed.auto()
                if m["emoji"]["name"]=='🤙':
                    time.sleep(random.randint(2, 4))
                    channelID = m["channel_id"]
                    messageID = m["message_id"]
                    self.bot.addReaction(channelID, messageID, '🤙')

        @self.bot.gateway.command
        def respond(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                username = m["author"]["username"]
                discriminator = m["author"]["discriminator"]
                id = self.bot.gateway.session.user["id"]
                content = m["content"]
                timestamp = self.timestamp_parse(m["timestamp"])
                
                mentioned = False
                for i in m["mentions"]:
                    if id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]
                mentioned_towrite = "[MENTIONED] " if mentioned else ''

                triggered = self.is_triggered(content)
                triggered_towrite = "[TRIGGERED] " if triggered else ''

                print("> {}{}{} | {} | {}#{}: {}".format(triggered_towrite, mentioned_towrite, channelID, timestamp, username, discriminator, content))

                himself = (m["author"]["id"] == id)

                if not himself and channelID in self.allowed_channels: 
                    if mentioned:
                        self.bot.reply(channelID, msg_id, self.response(channelID))
                    elif triggered:
                        self.bot.sendMessage(channelID, self.response(channelID))
          
        self.bot.gateway.run(auto_reconnect=True)



if __name__ == '__main__':

    def bot_launch():
        global bot
        bot = Bot()

        global thread
        thread = Thread(target=bot.main_launch)
        thread.start()

    def bot_kill():
        global bot
        bot.kill_genai()
        bot.bot.gateway.close()
        thread.join()
        print("\n>>> Соединение сброшено.\n")

    def MSKtoEU_timezone(time_MSK):
        hour = int(time_MSK[0:2]) - 3
        minute = time_MSK[3:5]
        if hour < 0:
            hour += 24
        if hour < 10:
            hour = str('0' + hour)
        else:
            hour = str(hour)
        return hour + ':' + minute

    
    launch_time = MSKtoEU_timezone(os.getenv("LAUNCH_TIME"))
    kill_time = MSKtoEU_timezone(os.getenv("KILL_TIME"))

    schedule.every().day.at(launch_time).do(bot_launch)
    schedule.every().day.at(kill_time).do(bot_kill)

    while True:
        schedule.run_pending()
