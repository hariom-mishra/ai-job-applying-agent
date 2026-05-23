from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    openaikey: str

config: Setting = None

def getSettings() -> Setting:
    global config
    if config is None:
        config = Setting()
    return config

