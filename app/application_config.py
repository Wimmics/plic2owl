import logging
import yaml

"""This module loads the YAML configuration file (/config/application.yml) at starup
and provides a function to retrive a confirgation parameter.
"""
logger = logging.getLogger("app." + __name__)

with open("../config/application.yml", "r") as cfg:
    config = yaml.load(cfg, Loader=yaml.FullLoader)


def get(key: str) -> str:
    """Return the value of a configuration parameter"""

    if key not in config.keys():
        logger.warning(f"Paramter {key} not found in configuration")
        return None
    else:
        return config.get(key)
