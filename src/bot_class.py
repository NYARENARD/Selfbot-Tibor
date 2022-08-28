import discum
from threading import Thread
import random
from googletrans import Translator
from googletrans import LANGUAGES
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
import requests
import os

class Bot(Thread):
    
    def __init__(self, cfg):
        Thread.__init__(self)
        self._token = cfg["token"]
        self._owner_id = cfg["owner_id"]
        self._channels = cfg["channels"]
        self._prefix = cfg["prefix"]
        self._log_channel = cfg["logchannel"]
        self._auto_trans_chs = cfg["auto_trans_chs"] 

        self.bot = discum.Client(token = self._token, log=False)
        #chrome_options = webdriver.ChromeOptions()
        #chrome_options.binary_location = cfg["binary_location"]
        #chrome_options.add_argument("--headless")
        #chrome_options.add_argument("--disable-dev-shm-usage")
        #chrome_options.add_argument("--no-sandbox")
        #chrome_options.add_argument("--start-maximized")
        #self._browser = webdriver.Chrome(executable_path=cfg["executable_location"], chrome_options=chrome_options)
        self._logging("`>>> `<@" + self._owner_id + ">`" + " Подключение успешно.`", [])

    def __del__(self):
        self.bot.gateway.close()
        #self._browser.quit()
        self._logging(">>> Соединение бота сброшено.\n", [])

    def run(self):
        self._bot_launch()
	
    def _logging(self, message, attachments):
        print(message)
        self.bot.sendMessage(self._log_channel, message)
        for url in attachments:
            self.bot.sendFile(self._log_channel, url, isurl=True) 


    
    def _bot_launch(self):

        command_list = ["трансстарт", "трансстоп", "автотранслейт", "потегам"]
        flag_trans_gl = 1
        flag_autotrans_gl = 0

        def command_handle(command_name, channelID, messageID):
            nonlocal flag_trans_gl
            nonlocal flag_autotrans_gl
            if command_name == "трансстарт":
                flag_trans_gl = 1
            elif command_name == "трансстоп":
                flag_trans_gl = 0
            elif command_name == "автотранслейт":
                flag_autotrans_gl = 1
            elif command_name == "потегам":
                flag_autotrans_gl = 0
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
                            self.bot.typingAction(channelID)
                            self.bot.sendMessage(channelID, translation.text)

        @self.bot.gateway.command
        def translate_msg(resp):
            if resp.event.message and flag_trans_gl:
                m = resp.parsed.auto()
                channelID = m["channel_id"]
                messageID = m["id"]
                content = m["content"]
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)
                try:
                    ref_msg = m["referenced_message"]
                except:
                    return
                if ref_msg == None:
                    return
                ref_content = ref_msg["content"]
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
                        if not (len(content) == 1 and "<@" + self_id + ">" in content[0]):
                            if len(content) > 1:
                                dst_lang_raw = content[1]
                            elif "<@" + self_id + ">" not in content[0]:
                                dst_lang_raw = content[0]
                            dst_lang = translator.translate(dst_lang_raw, dest="en").text.lower()
                            try:
                                lang_code = inv_langs[dst_lang]
                            except:
                                self.bot.addReaction(channelID, messageID, '❔')
                        else:
                            lang_code = "ru"
                        translation = translator.translate(ref_content, dest=lang_code)
                        self.bot.typingAction(channelID)
                        self.bot.reply(channelID, msg_id, translation.text)
                  
        #@self.bot.gateway.command             TO BE REPAIRED
        #def translate_reaction(resp):
        #    if resp.event.reaction_added and flag_trans_gl:
        #        m = resp.parsed.auto()
        #        channelID = m["channel_id"]
        #        ref_msg = m["message_id"]
        #        try:
        #            ref_content = ref_msg["content"]
        #        except:
        #            ref_content = m["content"]   ПО ИВЕНТУ РЕАКЦИИ НЕТ КОНТЕНТА      
        #        
        #         
        #        if m["emoji"]["name"]=='🔰':
        #            if ref_content:
        #                translator = Translator()
        #                lang_code = "ru"
        #                translation = translator.translate(ref_content, dest=lang_code)
        #                self.bot.typingAction(channelID)
        #                self.bot.sendMessage(channelID, translation.text)

        self.bot.gateway.run()

