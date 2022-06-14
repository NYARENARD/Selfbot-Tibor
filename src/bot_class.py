import discum
from threading import Thread
import time
import random
from googletrans import Translator
from googletrans import LANGUAGES
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os

class Bot:
    
    def __init__(self, cfg):
        self._token = cfg["token"]
        self._owner_id = cfg["owner_id"]
        self._database = cfg["database"]
        self._trigger = cfg["trigger"]
        self._channels = cfg["channels"]
        self._prefix = cfg["prefix"]
        self._log_channel = cfg["logchannel"]
        self._auto_trans_chs = cfg["auto_trans_chs"] 

        self.bot = discum.Client(token = self._token, log=False)
        self._thread = Thread(target=self._commands_launch)
        self._thread.start()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = cfg["binary_location"]
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        self._browser = webdriver.Chrome(executable_path=cfg["executable_location"], chrome_options=chrome_options)
        self.bot.sendMessage(self._log_channel, "<@" + self._owner_id + ">")
        self._logging("\n>>> Подключение успешно.\n", [])

    def __del__(self):
        self.bot.gateway.close()
        self._thread.join()
        self._browser.quit()
        self._logging("\n>>> Соединение сброшено.\n", [])
	
    def _logging(self, message, attachments):
        print(message)
        self._type_send(self._log_channel, '`' + message + '`', attachments)

    def _type_send(self, channelID, message, attachments):
        self.bot.typingAction(channelID)
        self.bot.sendMessage(channelID, message)
        for url in attachments:
            self.bot.sendFile(channelID, url, isurl=True) 


    
    def _commands_launch(self):

        command_list = {self._prefix + "чатстарт" : ["чатстарт", "Привет."],\
                        self._prefix + "чатстоп" : ["чатстоп", "Принял."],\
                        self._prefix + "реактстарт" : ["реактстарт", "Ставлю реакции."],\
                        self._prefix + "реактстоп" : ["реактстоп", "Не ставлю реакции."],\
                        self._prefix + "трансстарт" : ["трансстарт", "Перевожу с UA на RU."],\
                        self._prefix + "трансстоп" : ["трансстоп", "Не перевожу."],\
                        self._prefix + "автотранслейт" : ["автотранслейт", "Перевожу автоматически с UA на RU."],\
                        self._prefix + "потегам" : ["потегам", "Перевожу только по тегам."]}
        flag_resp_gl = 0
        flag_rea_gl = 0
        flag_trans_gl = 1
        flag_autotrans_gl = 0

        def command_handle(config, channelID):
            command_name = config[0]
            ans_gotit = config[1]
            nonlocal flag_resp_gl
            nonlocal flag_rea_gl
            nonlocal flag_trans_gl
            nonlocal flag_autotrans_gl
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
            elif command_name == "автотранслейт":
                flag_autotrans_gl = 1
            elif command_name == "потегам":
                flag_autotrans_gl = 0
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
        def translate_auto(resp):
            if resp.event.message and flag_trans_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                content = m["content"]
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)
                
                if channelID in self._auto_trans_chs or flag_autotrans_gl:
                    translator = Translator()
                    languages = translator.detect([content])
                    for lang in languages:
                        if lang.lang == "uk" and not himself:
                            translation = translator.translate(content, dest="ru")
                            self._type_send(channelID, translation.text, [])

        @self.bot.gateway.command
        def translate(resp):
            if resp.event.message and flag_trans_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                content = m["content"]
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)
                ref_msg = m["referenced_message"]
                if ref_msg == None:
                    return
                try:
                    ref_content = ref_msg["content"]
                except:
                    ref_content = None
                attachments = []
                for dict in ref_msg['attachments']:
                    attachments.append(dict['url'])
                
                mentioned = False
                for i in m["mentions"]:
                    if self_id == i["id"]:
                        mentioned = True
                        msg_id = m["id"]
                 
                if mentioned:
                    if ref_content:
                        translator = Translator()
                        inv_langs = {v: k for k, v in LANGUAGES.items()}
                        content = content.split(' ')
                        if not (len(content) == 1 and "<@" in content[0]):
                            if len(content) > 1:
                                dst_lang_raw = content[1]
                            elif "<@" not in content[0]:
                                dst_lang_raw = content[0]
                            dst_lang = translator.translate(dst_lang_raw, dest="en").text.lower()
                            lang_code = inv_langs[dst_lang]
                        else:
                            lang_code = "ru"
                        translation = translator.translate(ref_content, dest=lang_code)
                        self.bot.typingAction(channelID)
                        self.bot.reply(channelID, msg_id, translation.text)
                    
                    if attachments != []:
                        for attch in attachments:
                            url_to_download = attch
                            r = requests.get(url_to_download)
                            with open('attachment.png', 'wb') as f: 
                                f.write(r.content)
                            self._browser.get("https://translate.yandex.ru/ocr")
                            while not fileInput:
                                try:
                                    accept_btn = self._browser.find_element_by_xpath("//*[contains(text(), 'Accept')]").click()
                                except:
                                    pass
                                try:
                                    fileInput = self._browser.find_element_by_xpath("//input[@type='file']")
                                except:
                                    self._browser.refresh()
                            filePath = os.getcwd() + "/attachment.png"
                            fileInput.send_keys(filePath)
                            self._browser.implicitly_wait(3)
                            image = self._browser.find_element(By.CSS_SELECTOR, "image")
                            image.screenshot("screenshot.png")
                            #self._browser.save_screenshot("screenshot.png")
                            image_link = os.getcwd() + "/screenshot.png"
                            self.bot.sendFile(channelID, image_link, isurl=False)




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
                    if not himself and channelID in self._channels and not bot_flag: 
                        if mentioned:
                            self.bot.typingAction(channelID)
                            self.bot.reply(channelID, msg_id, self._rndm_response())
                        elif triggered:
                            self._type_send(channelID, self._rndm_response(), [])

        self.bot.gateway.run()

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
