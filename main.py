import discum
import time
import random
import schedule
import os
from threading import Thread

class Bot:

    def __init__(self, token, database, trigger, channels):
        self._token = token
        self._database = database
        self._trigger = trigger
        self._channels = channels

        self.bot = discum.Client(token = self._token, log=False)           #не приват
        self._thread = Thread(target=self._commands_launch)
        self._thread.start()
        print("\n>>> Подключение успешно.\n")
        self._enable_genai()

    def __del__(self):
        self._kill_genai()
        self.bot.gateway.close()
        self._thread.join()
        print("\n>>> Соединение сброшено.\n")
	
		
    def _enable_genai(self):
        self.bot.sendMessage("730552031735054337", "g.interval random")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen +")
	
    def _kill_genai(self):
        self.bot.sendMessage("730552031735054337", "g.interval off")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen -")


    def _is_triggered(self, content):
        with open(self._trigger, 'r', encoding="utf-8") as f:
            for line in f:
                if line.strip() in content.lower():
                    return True
        return False  

    def _response(self, channelID):
        time.sleep(random.randint(4, 8))
        self.bot.typingAction(channelID)
        with open(self._database, 'r', encoding="utf-8") as f:
            base_ar = f.read().split('\n')
            to_send = random.choice(base_ar)
            time.sleep(len(to_send) // 6 + 1)
            return to_send

    def _timestamp_parse(self, raw):
        sec = raw[17:22]
        minu = raw[14:16]
        hr = int(raw[11:13]) + 3
        day = str(int(raw[8:10]) + hr // 24)
        hr = str(hr % 24)
        mon = raw[5:7]
        year = raw[0:4]
        timestamp = hr+':'+minu+':'+sec+' '+day+'-'+mon+'-'+year
        return timestamp


    def _commands_launch(self):

        @self.bot.gateway.command
        def reaction_add(resp):
            if resp.event.reaction_added:
                m = resp.parsed.auto()
                if m["emoji"]["name"]=='🤙':
                    channelID = m["channel_id"]
                    messageID = m["message_id"]
                    id = self.bot.gateway.session.user["id"]
                    time.sleep(1)
                    self.bot.addReaction(channelID, messageID, '🤙')

                    himself = (m["member"]["user"]["id"] == id)
                    if not himself:
                        print("> {} | {} | 🤙".format(channelID, messageID))
                    #self.bot.sendMessage("730552031735054337", "> {} | {} | 🤙".format(channelID, messageID))

        @self.bot.gateway.command
        def respond(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                username = m["author"]["username"]
                discriminator = m["author"]["discriminator"]
                self_id = self.bot.gateway.session.user["id"]
                content = m["content"]
                timestamp = self._timestamp_parse(m["timestamp"])
                try:
                    bot_flag = m["author"]["bot"]
                except Exception:
                    bot_flag = False
                
                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]
                mentioned_towrite = "[MENTIONED] " if mentioned else ''

                triggered = self._is_triggered(content)
                triggered_towrite = "[TRIGGERED] " if triggered else ''

                print("> {}{}{} | {} | {}#{}: {}".format(triggered_towrite, mentioned_towrite, channelID, timestamp, username, discriminator, content))

                himself = (m["author"]["id"] == self_id)

                if not himself and channelID in self._channels and not bot_flag: 
                    if mentioned:
                        self.bot.reply(channelID, msg_id, self._response(channelID))
                    elif triggered:
                        self.bot.sendMessage(channelID, self._response(channelID))
          
        self.bot.gateway.run(auto_reconnect=True)



if __name__ == '__main__':
    
    def bot_launch():
        global instance
        instance = Bot(token, database, trigger, channels)

    def bot_kill():
        global instance
        instance.__del__()
        instance = None

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

    token = os.getenv("TOKEN")
    database = os.getenv("DATABASE_NAME")
    trigger = os.getenv("TRIGGER_NAME")
    channels = os.getenv("CHANNELS").split()
    
    launch_time = MSKtoEU_timezone(os.getenv("LAUNCH_TIME"))
    kill_time = MSKtoEU_timezone(os.getenv("KILL_TIME"))

    schedule.every().day.at(launch_time).do(bot_launch)
    schedule.every().day.at(kill_time).do(bot_kill)

    while True:
        schedule.run_pending()