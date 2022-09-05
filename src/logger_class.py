import discum
from threading import Thread
import time

class Logger(Thread):
    
    def __init__(self, cfg):
        Thread.__init__(self)
        self._token = cfg["token"]
        self._prefix = cfg["prefix"]
        self._log_channel = cfg["logchannel"]
        self.bot = discum.Client(token = self._token, log=False)

    def __del__(self):
        self.bot.gateway.close()
        self._logging("msg", "`>>> Соединение логгера сброшено.`")
	
    def run(self):
        self._logger_launch()

    def _logging(self, type, content, attachments = [], reference = ""):
        print(content)
        time.sleep(1)
        if type == "msg":
            self.bot.sendMessage(self._log_channel, content)
        elif type == "rpl":
            self.bot.reply(self._log_channel, reference, content)
        for url in attachments:
            payload = "`URL:  " + "{}`".format(url)
			time.sleep(1)
            self.bot.sendMessage(self._log_channel, payload)
			time.sleep(1)
            self.bot.sendFile(self._log_channel, url, isurl=True)

    
    def _logger_launch(self):

        command_list = ["логировать", "нелогировать", "разрешить", "запретить"]
        flag_log_gl = 1
        flag_permission_gl = 1

        def command_handle(command_name, channelID, messageID):
            nonlocal flag_log_gl
            nonlocal flag_permission_gl
            if command_name == "логировать":
                flag_log_gl = 1
            elif command_name == "нелогировать":
                flag_log_gl = 0 
            elif command_name == "разрешить":
                flag_permission_gl = 1
            elif command_name == "запретить":
                flag_permission_gl = 0  
            else:
                self.bot.addReaction(channelID, messageID, '❔')
                return
            self.bot.addReaction(channelID, messageID, '✅')

        @self.bot.gateway.command
        def read_command(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                messageID = m["id"]
                content = m["content"]

                for command in command_list:
                    if content.lower() == self._prefix + command:
                        command_handle(command_list[command], channelID, messageID)
                        return

        @self.bot.gateway.command
        def log_messages(resp):
            if resp.event.message and flag_log_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                msg_id = m["id"]
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
                command_towrite = 'C' if self._prefix + content in command_list else ''
                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        break
                mentioned_towrite = 'M' if mentioned else ''

                if not bot_flag and channelID != self._log_channel:
                    payload = "`MSG " + "`||`[{}{}]".format(command_towrite, mentioned_towrite).rjust(4) + ' ' + \
                              "{}".format(channelID).rjust(18) + " | " + "{}".format(timestamp).rjust(22) + " | " + \
                              "{}".format(msg_id).rjust(18) + " | `||`" + "{}#{}".format(username, discriminator).rjust(21) + \
                              "` **Replied**: `" + " {}`".format(content)
                    if m["referenced_message"] != None:
                        searchResponse = self.bot.searchMessages(channelID=self._log_channel, textSearch=m["referenced_message"]["id"])
                        results = self.bot.filterSearchResults(searchResponse)
                        try:
                            ref_msg = results[0]["id"]
                            self._logging("rpl", payload, attachments, ref_msg)							
                        except:
                            self._logging("msg", payload, attachments)   
                    else:
                        payload = "`MSG " + "`||`[{}{}]".format(command_towrite, mentioned_towrite).rjust(4) + ' ' + \
                                  "{}".format(channelID).rjust(18) + " | " + "{}".format(timestamp).rjust(22) + " | " + \
                                  "{}".format(msg_id).rjust(18) + " | `||`" + "{}#{}".format(username, discriminator).rjust(21) + \
                                  ": " + " {}`".format(content)
                        self._logging("msg", payload, attachments)

        @self.bot.gateway.command
        def log_delete(resp):
            if resp.event.message_deleted and flag_log_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                msg_id = m["id"]
                if channelID != self._log_channel:
                    payload = "`DEL " + "`||`{}".format(channelID).rjust(18) + \
                              " | " + "{}".format(msg_id).rjust(18) + "`|| ** Deleted**"
                    searchResponse = self.bot.searchMessages(channelID=self._log_channel, textSearch=msg_id)
                    results = self.bot.filterSearchResults(searchResponse)
                    try:
                        deleted_msg = results[0]["id"] 
                        self._logging("rpl", payload, reference=deleted_msg) 
                    except:
                        self._logging("msg", payload)

        @self.bot.gateway.command
        def log_update(resp):
            if resp.event.message_updated and flag_log_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                msg_id = m["id"]
                content = m["content"]
                if channelID != self._log_channel:
                    payload = "`UPD " + "`||`{}".format(channelID).rjust(18) + \
                              " | " + "{}".format(msg_id).rjust(18) + "`|| ** Updated**: `" + content + '`'
                    searchResponse = self.bot.searchMessages(channelID=self._log_channel, textSearch=msg_id)
                    results = self.bot.filterSearchResults(searchResponse)
                    try:
                        updated_msg = results[0]["id"] 
                        self._logging("rpl", payload, reference=updated_msg) 
                    except:
                        self._logging("msg", payload)

                
        @self.bot.gateway.command
        def logchannel_commands(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]  
                messageID = m["id"]
                content = m["content"]
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)
                attachments = []
                for dict in m['attachments']:
                    attachments.append(dict['url'])

                if channelID == self._log_channel and flag_permission_gl:
                    content_arr = content.split(' ', 2)
                    command = content_arr[0].lower()
                    
                    if command == "отправить":
                        channel = content_arr[1] 
                        content = content_arr[2]
                        time_to_wait = len(content) // 5 + 1 
                        self.bot.addReaction(channelID, messageID, '💬') 
                        t = Thread(target=self._imit, args=(channel, time_to_wait))
                        t.start()
                        t.join()
                        self.bot.sendMessage(channel, content)
                        for url in attachments:
                            self.bot.sendFile(channel, url, isurl=True)
                        self.bot.addReaction(channelID, messageID, '✅') 
                    elif command == "удалить":
                        if m["referenced_message"] != None:
                            ref_arr = m["referenced_message"]["content"].split(' ', 10)
                            channel = ref_arr[2]
                            msg_id = ref_arr[9] 
                        else:
                            channel = content_arr[1] 
                            msg_id = content_arr[2]
                        self.bot.deleteMessage(channel, msg_id)
                        self.bot.addReaction(channelID, messageID, '✅') 
                    elif command == "ответить":
                        if m["referenced_message"] != None:
                            ref_arr = m["referenced_message"]["content"].split(' ', 10)
                            channel = ref_arr[2]
                            msg_id = ref_arr[9]
                            try:
                                content = content_arr[1] + ' ' + content_arr[2]
                            except:
                                content = content_arr[1]
                        else:
                            extra_arr = content_arr[2].split(' ', 1)
                            channel = content_arr[1] 
                            msg_id = extra_arr[0]
                            content = extra_arr[1]
                        time_to_wait = len(content) // 5 + 1 
                        self.bot.addReaction(channelID, messageID, '💬') 
                        t = Thread(target=self._imit, args=(channel, time_to_wait))
                        t.start()
                        t.join()
                        self.bot.reply(channel, msg_id, content)
                        for url in attachments:
                            self.bot.sendFile(channel, url, isurl=True) 
                        self.bot.addReaction(channelID, messageID, '✅') 
                    elif command == "редактировать":
                        if m["referenced_message"] != None:
                            ref_arr = m["referenced_message"]["content"].split(' ', 10)
                            channel = ref_arr[2]
                            msg_id = ref_arr[9]
                            try:
                                content = content_arr[1] + ' ' + content_arr[2]
                            except:
                                content = content_arr[1]
                        else:
                            extra_arr = content_arr[2].split(' ', 1)
                            channel = content_arr[1] 
                            msg_id = extra_arr[0]
                            message = extra_arr[1]
                        self.bot.editMessage(channel, msg_id, message) 
                        self.bot.addReaction(channelID, messageID, '✅') 

        @self.bot.gateway.command
        def into_file(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]  
                messageID = m["id"]
                content = m["content"].lower()
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)

                if channelID == self._log_channel and flag_permission_gl and not himself:
                    content_arr = content.split(' ', 3)
                    command = content_arr[0]
                    filename = content_arr[1]
                    file_height = int(content_arr[2])
                    request = content_arr[3]

                    if command == "оформить":
                        self.bot.addReaction(channelID, messageID, '💬')
                        num_processed = 0
                        h_temp = file_height
                        with open(filename, 'w', encoding="utf-8") as f:
                            while num_processed < file_height:
                                if h_temp >= 25:
                                    diff = 25 
                                else:
                                    diff = h_temp
                                h_temp -= diff
                                try:
                                    searchResponse = self.bot.searchMessages(channelID=self._log_channel, textSearch=request, afterNumResults=num_processed, limit=diff)
                                    results = self.bot.filterSearchResults(searchResponse)
                                except KeyError:
                                    break
                                for message in results:
                                    to_input = message["content"]
                                    to_input = to_input.replace('`', '')
                                    to_input = to_input.replace('||', '')
                                    f.write(to_input + '\n')
                                num_processed += diff

                        self.bot.sendFile(self._log_channel, filename, isurl=False)
                        self.bot.addReaction(channelID, messageID, '✅')
                        import os
                        os.remove(filename)

                            

        def _imit(self, channel, time_to_wait):
            for counter in range(time_to_wait):
                self.bot.typingAction(channel)
                time.sleep(1)

        self.bot.gateway.run()

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
