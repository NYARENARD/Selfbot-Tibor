import discum
import time
import random
import schedule
import os
from threading import Thread

class Bot:

    def __init__(self, token, database, trigger, channels, prefix):
        self._token = token
        self._database = database
        self._trigger = trigger
        self._channels = channels
        self._prefix = prefix

        self.bot = discum.Client(token = self._token, log=False)
        self._thread = Thread(target=self._commands_launch)
        self._thread.start()
        self._logging("\n>>> Подключение успешно.\n")
        self._genaiflag = 0

    def __del__(self):
        self.bot.gateway.close()
        self._thread.join()
        self._logging("\n>>> Соединение сброшено.\n")
	
    def _logging(self, message):
        print(message)
        self.bot.sendMessage("937728682464788480", message)

    def genai_enable(self):
        if self._genaiflag:
            return
        self.bot.sendMessage("730552031735054337", "g.interval random")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen +")
        self._genaiflag = 1
	
    def genai_kill(self):
        if not self._genaiflag:
            return
        self.bot.sendMessage("730552031735054337", "g.interval off")
        time.sleep(1)
        self.bot.sendMessage("730552031735054337", "g.config mention_gen -")
        self._genaiflag = 0


    
    def _commands_launch(self):

        command_list = {self._prefix + "чатстарт" : [1, None, "Привет.", "Я и так уже разговариваю."],\
                        self._prefix + "чатстоп" : [0, None, "Принял, отчаливаю.", "Когда волк молчит - лучше его не перебивать."],\
                        self._prefix + "реактстарт" : [None, 1, "Ставлю реакции.", "Я и так уже ставлю реакции."],\
                        self._prefix + "реактстоп" : [None, 0, "Не ставлю реакции.", "Я и так реакции не ставлю."],\
                        self._prefix + "генаистарт" : [None, None, "genaistart", "Генаи уже работает."],\
                        self._prefix + "генаистоп" : [None, None, "genaistop", "Генаи все еще не работает."]}
        flag_resp_gl = 1
        flag_rea_gl = 0

        def command_handle(config, channelID):
            flag_resp = config[0]
            flag_rea = config[1]
            ans_gotit = config[2]
            ans_nonsense = config[3]

            nonlocal flag_resp_gl
            nonlocal flag_rea_gl

            if flag_resp != None:
                if flag_resp == flag_resp_gl:
                    self.bot.sendMessage(channelID, ans_nonsense)
                else:
                    flag_resp_gl = flag_resp
                    self.bot.sendMessage(channelID, ans_gotit)

            if flag_rea != None:
                if flag_rea == flag_rea_gl:
                    self.bot.sendMessage(channelID, ans_nonsense)
                else:
                    flag_rea_gl = flag_rea
                    self.bot.sendMessage(channelID, ans_gotit)

            if ans_gotit == "genaistart":
                if self._genaiflag:
                    self.bot.sendMessage(channelID, ans_nonsense)
                else:
                    self.genai_enable()

            if ans_gotit == "genaistop":
                if not self._genaiflag:
                    self.bot.sendMessage(channelID, ans_nonsense)
                else:
                    self.genai_kill()

        @self.bot.gateway.command
        def read_command(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                content = m["content"]

                for command in command_list:
                    if content == command:
                        command_handle(command_list[command], channelID)

        @self.bot.gateway.command
        def reaction_add(resp):
            if resp.event.reaction_added:
                m = resp.parsed.auto()
                if m["emoji"]["name"]=='🤙':
                    channelID = m["channel_id"]
                    messageID = m["message_id"]
                    id = self.bot.gateway.session.user["id"]
                    if flag_rea_gl:
                        time.sleep(1)
                        self.bot.addReaction(channelID, messageID, '🤙')

                    himself = (m["member"]["user"]["id"] == id)
                    if not himself:
                        self._logging("> {} | {} | 🤙".format(channelID, messageID))

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

                command_towrite = "[COMMAND] " if content in command_list else ''
                
                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]
                mentioned_towrite = "[MENTIONED] " if mentioned else ''

                triggered = self._is_triggered(content)
                triggered_towrite = "[TRIGGERED] " if triggered else ''

                forbidden_towrite = "[FORBIDDEN] " if (triggered or mentioned) and not flag_resp_gl else ''

                if not bot_flag:
                    self._logging("> {}{}{}{}{} | {} | {}#{}: {}".format(command_towrite, forbidden_towrite, triggered_towrite, mentioned_towrite,\
                                                                 channelID, timestamp, username, discriminator, content))

                himself = (m["author"]["id"] == self_id)

                if flag_resp_gl:
                    if not himself and channelID in self._channels and not bot_flag: 
                        if mentioned:
                            self.bot.reply(channelID, msg_id, self._response(channelID))
                        elif triggered:
                            self.bot.sendMessage(channelID, self._response(channelID))
          
        self.bot.gateway.run(auto_reconnect=True)


    def _is_triggered(self, content):
        with open(self._trigger, 'r', encoding="utf-8") as f:
            for line in f:
                if line.strip() in content.lower():
                    return True
        return False  

    def _response(self, channelID):
        time.sleep(random.randint(3, 5))
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




if __name__ == '__main__':

    def msktoeu_timezone(time_MSK):
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
    prefix = os.getenv("PREFIX")

    instance = Bot(token, database, trigger, channels, prefix)

    launch_time = msktoeu_timezone(os.getenv("LAUNCH_TIME"))
    kill_time = msktoeu_timezone(os.getenv("KILL_TIME"))

    schedule.every().day.at(launch_time).do(instance.genai_enable)
    schedule.every().day.at(kill_time).do(instance.genai_kill)

    while True:
        schedule.run_pending()