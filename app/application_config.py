"""
This module loads the YAML configuration file at starup
and provides a function to retrive a confirgation parameter.

Author: Franck Michel, Université Côte d'Azur, CNRS, Inria
Created: Aug. 2024
"""

import logging
import yaml


logger = logging.getLogger("app." + __name__)


def init(config_file: str) -> None:
    """Load a configuration file"""
    global config
    logger.info(f"Loading configuration file {config_file}")
    with open(config_file, "r") as cfg:
        config = yaml.load(cfg, Loader=yaml.FullLoader)


def get(key: str) -> str:
    """Return the value of a configuration parameter"""

    if key not in config.keys():
        logger.warning(f"Paramter {key} not found in configuration")
        return None
    else:
        return config.get(key)
