import discum
import time
import random
#import schedule
import os
from threading import Thread


class Bot:

    def __init__(self, token, database, trigger, channels, prefix, logchannel, guildID, roleID):
        self._token = token
        self._database = database
        self._trigger = trigger
        self._channels = channels
        self._prefix = prefix
        self._log_channel = logchannel
        self._guildID = guildID
        self._roleID = roleID

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
        self._type_send(self._log_channel, '`' + message + '`')

    def _type_send(self, channelID, message):
        self.bot.typingAction(channelID)
        self.bot.sendMessage(channelID, message)

    def genai_enable(self):
        if self._genaiflag:
            return
        self._type_send("730552031735054337", "g.interval random")
        time.sleep(1)
        self._type_send("730552031735054337", "g.config mention_gen +")
        self._genaiflag = 1
	
    def genai_kill(self):
        if not self._genaiflag:
            return
        self._type_send("730552031735054337", "g.interval off")
        self._type_send("730552031735054337", "g.config mention_gen -")
        self._genaiflag = 0


    
    def _commands_launch(self):

        command_list = {self._prefix + "чатстарт" : [1, None, "Привет.", "Я уже разговариваю."],\
                        self._prefix + "чатстоп" : [0, None, "Принял, отчаливаю.", "Когда волк молчит - лучше его не перебивать."],\
                        self._prefix + "реактстарт" : [None, 1, "Ставлю реакции.", "Я и так уже ставлю реакции."],\
                        self._prefix + "реактстоп" : [None, 0, "Не ставлю реакции.", "Я и так реакции не ставлю."],\
                        self._prefix + "генаистарт" : [None, None, "genaistart", "Генаи уже работает."],\
                        self._prefix + "генаистоп" : [None, None, "genaistop", "Генаи и так не работает."]}
        flag_resp_gl = 0
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
                    self._type_send(channelID, ans_nonsense)
                else:
                    flag_resp_gl = flag_resp
                    self._type_send(channelID, ans_gotit)

            if flag_rea != None:
                if flag_rea == flag_rea_gl:
                    self._type_send(channelID, ans_nonsense)
                else:
                    flag_rea_gl = flag_rea
                    self._type_send(channelID, ans_gotit)

            if ans_gotit == "genaistart":
                if self._genaiflag:
                    self._type_send(channelID, ans_nonsense)
                else:
                    self.genai_enable()

            if ans_gotit == "genaistop":
                if not self._genaiflag:
                    self._type_send(channelID, ans_nonsense)
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
                if m["emoji"]["name"]=='🤙' and flag_rea_gl:
                    channelID = m["channel_id"]
                    messageID = m["message_id"]
                    self.bot.addReaction(channelID, messageID, '🤙')

        @self.bot.gateway.command
        def role_add(resp):
            if resp.event.presence_updated:
                m = resp.parsed.auto()
                try:
                    username = m['user']['username']
                except:
                    return
                userid = m['user']['id']
                try:
                    activity = m['activities'][1]['name']
                except:
                    activity = m['activities'][0]['name']
                print('{}: {}'.format(username, activity))
                if activity in banlist:
                    self._give_role(guildID, userid, username, roleID)
                    self._logging('Role: {}'.format(username))
                    self.bot.sendMessage(948531764643627069, 'Участник: {}\nПричина: {}'.format(username, activity))

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
                except:
                    bot_flag = False
                
                command_towrite = 'C' if content in command_list else ''

                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]
                mentioned_towrite = 'M' if mentioned else ''

                triggered = self._is_triggered(content)
                triggered_towrite = 'T' if triggered else ''

                forbidden_towrite = 'F' if (triggered or mentioned) and not flag_resp_gl else ''

                himself = (m["author"]["id"] == self_id)

                if not bot_flag and channelID != self._log_channel:
                    self._logging('> ' + "[{}{}{}{}]".format(command_towrite, forbidden_towrite, triggered_towrite, mentioned_towrite).rjust(6) + ' ' + \
                                  "{}".format(channelID).rjust(18) + " | " + "{}".format(timestamp).rjust(22) + " | " + \
                                  "{}#{}".format(username, discriminator).rjust(19 if '🎷' in username else 20) + ": " + " {}".format(content))

                if flag_resp_gl:
                    time.sleep(2)
                    if not himself and channelID in self._channels and not bot_flag: 
                        if mentioned:
                            self.bot.typingAction(channelID)
                            self.bot.reply(channelID, msg_id, self._rndm_response())
                        elif triggered:
                            self._type_send(channelID, self._rndm_response())

        self.bot.gateway.run()

    def _give_role(self, guildID, memberID, username, roleID):
        self.bot.addMembersToRole(guildID, roleID, [memberID])
        print(">>> Role given: {}".format(username))

    def _is_triggered(self, content):
        with open(self._trigger, 'r', encoding="utf-8") as f:
            for line in f:
                if line.strip() in content.lower():
                    return True
        return False  

    def _rndm_response(self):
        with open(self._database, 'r', encoding="utf-8") as f:
            base_ar = f.read().split('\n')
            to_send = random.choice(base_ar)
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

if __name__ == '__main__':
    token = os.getenv("TOKEN")
    database = os.getenv("DATABASE_NAME")
    trigger = os.getenv("TRIGGER_NAME")
    channels = os.getenv("CHANNELS").split()
    prefix = os.getenv("PREFIX")
    logchannel = os.getenv("LOGCHANNEL")
    banlist = os.getenv("BANLIST").split(',')
    guildID = os.getenv("GUILDID")
    roleID = os.getenv("ROLEID")

    instance = Bot(token, database, trigger, channels, prefix, logchannel, guildID, roleID)

    #launch_time = msktoeu_timezone(os.getenv("LAUNCH_TIME"))
    #kill_time = msktoeu_timezone(os.getenv("KILL_TIME"))
    #
    #schedule.every().day.at(launch_time).do(instance.genai_enable)
    #schedule.every().day.at(kill_time).do(instance.genai_kill)
    #
    #while True:
    #    schedule.run_pending()