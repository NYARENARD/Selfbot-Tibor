import discum
from threading import Thread
import time
import random
from googletrans import Translator

class Bot:
    
    def __init__(self, cfg):
        self._token = cfg["token"]
        self._database = cfg["database"]
        self._trigger = cfg["trigger"]
        self._channels = cfg["channels"]
        self._prefix = cfg["prefix"]
        self._log_channel = cfg["logchannel"]
        self._guildID = cfg["guildID"]
        self._channelID_to_fetch = cfg["channelID_to_fetch"]
        self._roleID = cfg["roleID"]
        self._banlist = cfg["banlist"]
        self._genai_channel = cfg["genai_channel"]
        self._shame_channel = cfg["shame_channel"]

        self.bot = discum.Client(token = self._token, log=False)
        self._thread = Thread(target=self._commands_launch)
        self._thread.start()
        self._logging("\n>>> Подключение успешно.\n", [])
        self._genaiflag = 0

    def __del__(self):
        self.bot.gateway.close()
        self._thread.join()
        self._logging("\n>>> Соединение сброшено.\n", [])
	
    def _logging(self, message, attachments):
        print(message)
        self._type_send(self._log_channel, '`' + message + '`', attachments)

    def _type_send(self, channelID, message, attachments):
        self.bot.typingAction(channelID)
        self.bot.sendMessage(channelID, message)
        for url in attachments:
            self.bot.sendFile(channelID, url, isurl=True)

    def genai_enable(self):
        self._type_send(self._genai_channel, "g.interval random", [])
        time.sleep(1)
        self._type_send(self._genai_channel, "g.config mention_gen +", [])
	
    def genai_kill(self):
        self._type_send(self._genai_channel, "g.interval off", []) 
        time.sleep(1)
        self._type_send(self._genai_channel, "g.config mention_gen -", []) 


    
    def _commands_launch(self):

        command_list = {self._prefix + "чатстарт" : ["чатстарт", "Привет."],\
                        self._prefix + "чатстоп" : ["чатстоп", "Принял."],\
                        self._prefix + "реактстарт" : ["реактстарт", "Ставлю реакции."],\
                        self._prefix + "реактстоп" : ["реактстоп", "Не ставлю реакции."],\
                        self._prefix + "генаистарт" : ["генаистарт", ""],\
                        self._prefix + "генаистоп" : ["генаистоп", ""],\
                        self._prefix + "трансстарт" : ["трансстарт", "Перевожу с UA на RU."],\
                        self._prefix + "трансстоп" : ["трансстоп", "Не перевожу."]}
        flag_resp_gl = 0
        flag_rea_gl = 0
        flag_trans_gl = 0

        def command_handle(config, channelID):
            command_name = config[0]
            ans_gotit = config[1]
            nonlocal flag_resp_gl
            nonlocal flag_rea_gl
            nonlocal flag_trans_gl
            if command_name == "чатстарт":
                flag_resp_gl = 1
            elif command_name == "чатстоп":
                flag_resp_gl = 0
            elif command_name == "реактстарт":
                flag_rea_gl = 1
            elif command_name == "реактстоп":
                flag_rea_gl = 0
            elif command_name == "трансстарт":
                flag_trans_gl = 1
            elif command_name == "трансстоп":
                flag_trans_gl = 0
            elif command_name == "генаистарт":
                self.genai_enable()
            elif command_name == "генаистоп":
                self.genai_kill()
            self._type_send(channelID, ans_gotit, []) 


        @self.bot.gateway.command
        def read_command(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                content = m["content"]

                for command in command_list:
                    if content.lower() == command:
                        command_handle(command_list[command], channelID)
                        break

        @self.bot.gateway.command
        def reaction_add(resp):
            if resp.event.reaction_added and flag_rea_gl:
                m = resp.parsed.auto()
                if m["emoji"]["name"]=='🤙':
                    channelID = m["channel_id"]
                    messageID = m["message_id"]
                    self.bot.addReaction(channelID, messageID, '🤙')
        
        @self.bot.gateway.command
        def translate(resp):
            if resp.event.message and flag_trans_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                content = m["content"]

                lang = Translator().detect(content)
                if lang == "uk":
                    translation = Translator().translate(content, dest="ru")
                    self.bot.typingAction(channelID)
                    self._type_send(channelID, translation.text, []) 


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
                self.bot.gateway.fetchMembers(self._guildID, self._channelID_to_fetch, keep="all")
                role_already_given = (self._roleID in self.bot.gateway.session.guild(self._guildID).members[userid]['roles'])

                if activity in self._banlist and not role_already_given:
                    self._give_role(self._guildID, userid, username, self._roleID)
                    self.bot.sendMessage(self._shame_channel, "Имя: {}\nID: {}\nПричина: {}".format(username, userid, activity))
                    self._logging("> Role given: {}".format(username), [])

        @self.bot.gateway.command
        def log(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                username = m["author"]["username"]
                discriminator = m["author"]["discriminator"]
                self_id = self.bot.gateway.session.user["id"]
                timestamp = self._timestamp_parse(m["timestamp"])
                content = m["content"]
                attachments = []
                for dict in m['attachments']:
                    attachments.append(dict['url'])

                try:
                    bot_flag = m["author"]["bot"]
                except:
                    bot_flag = False
                command_towrite = 'C' if content in command_list else ''
                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        break
                mentioned_towrite = 'M' if mentioned else ''
                triggered = self._is_triggered(content)
                triggered_towrite = 'T' if triggered else ''
                forbidden_towrite = 'F' if (triggered or mentioned) and not flag_resp_gl else ''

                if not bot_flag and channelID != self._log_channel:
                    self._logging('> ' + "[{}{}{}{}]".format(command_towrite, forbidden_towrite, triggered_towrite, mentioned_towrite).rjust(6) + ' ' + \
                                  "{}".format(channelID).rjust(18) + " | " + "{}".format(timestamp).rjust(23) + " | " + \
                                  "{}#{}".format(username, discriminator).rjust(20) + ": " + " {}".format(content), attachments)

        @self.bot.gateway.command
        def resend(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]  
                content = m["content"]
                attachments = []
                for dict in m['attachments']:
                    attachments.append(dict['url'])

                if channelID == self._log_channel:
                    channel = content[:18]
                    message = content[19:]
                    self.bot.sendMessage(channel, message)
                    for url in attachments:
                        self.bot.sendFile(channel, url, isurl=True)

        @self.bot.gateway.command
        def respond(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                self_id = self.bot.gateway.session.user["id"]
                content = m["content"]
                try:
                    bot_flag = m["author"]["bot"]
                except:
                    bot_flag = False

                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]

                triggered = self._is_triggered(content)

                himself = (m["author"]["id"] == self_id)

                if flag_resp_gl:
                    time.sleep(2)
                    if not himself and channelID in self._channels and not bot_flag: 
                        if mentioned:
                            self.bot.typingAction(channelID)
                            self.bot.reply(channelID, msg_id, self._rndm_response())
                        elif triggered:
                            self._type_send(channelID, self._rndm_response(), [])

        self.bot.gateway.run()

    def _give_role(self, guildID, memberID, roleID):
        self.bot.addMembersToRole(guildID, roleID, [memberID])

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
