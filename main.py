import discum
import time
import random
import os

bot = discum.Client(token = TOKEN, log=True)
print('\nПодключение успешно.\n')

def is_triggered(list, content):
    with open(list, 'r', encoding='utf-8') as read:
        for line in read:
            if line.strip() in content.lower():
                return True
        return False  

def response(channelID, base):
    time.sleep(random.randint(5, 8))
    bot.typingAction(channelID)
    with open(base, 'r', encoding='utf-8') as read:
        length = 0
        for line in read:
            length += 1
        rand = random.randint(1, length)
    with open(base, 'r', encoding='utf-8') as read:
        length = 0
        for line in read:
            length += 1
            if rand == length:
                time.sleep(len(line.rstrip('\n')) // 3)
                return line.rstrip('\n')

@bot.gateway.command
def main(resp):
    if resp.event.message:
        m = resp.parsed.auto()
        channelID = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        id = bot.gateway.session.user['id']
        content = m['content']
        
        mentioned = False
        for i in m['mentions']:
            if id == i['id']:
                mentioned = True
                msg_id = m['id']
        self = (m['author']['id'] != id)

        
        if self:
            if mentioned:
                bot.reply(channelID, msg_id, response(channelID, 'database.txt'))
            elif is_triggered('trigger.txt', content):
                bot.sendMessage(channelID, response(channelID, 'database.txt'))
                
        print("> channel {} | {}#{}: {}".format(channelID, username, discriminator, content))

bot.gateway.run(auto_reconnect=True)
