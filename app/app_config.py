import logging
import yaml

logger = logging.getLogger('app.' + __name__)

with open("../config/application.yml", "r") as cfg:
    config = yaml.load(cfg, Loader=yaml.FullLoader)

def get(key: str) -> str:
    if key not in config.keys():
        logger.warning(f"Paramter {key} not found in configuration")
        return None
    return config.get(key)
