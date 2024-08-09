import logging
import yaml

logger = logging.getLogger("app." + __name__)

with open("../config/application.yml", "r") as cfg:
    config = yaml.load(cfg, Loader=yaml.FullLoader)


def get(key: str) -> str:
    """Retrive parameters from the global configuration loaded from `config/application.yml`
    """
    if key not in config.keys():
        logger.warning(f"Paramter {key} not found in configuration")
        return None
    else:
        return config.get(key)
