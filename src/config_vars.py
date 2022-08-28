import os

class_vars = {
    "token" : os.getenv("TOKEN"),
    "owner_id" : os.getenv("OWNER_ID"),
    "channels" : os.getenv("CHANNELS").split(),
    "prefix" : os.getenv("PREFIX"),
    "logchannel" : os.getenv("LOGCHANNEL"),
    "auto_trans_chs" : os.getenv("AUTO_TRANS_CHS"),
    #"binary_location" : os.getenv("GOOGLE_CHROME_BIN"),
    #"executable_location" : os.getenv("CHROMEDRIVER_PATH")
}
