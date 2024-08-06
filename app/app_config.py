import yaml

with open("../config/application.yml", "r") as cfg:
    config = yaml.load(cfg, Loader=yaml.FullLoader)

def get(key: str):
    return config.get(key)
