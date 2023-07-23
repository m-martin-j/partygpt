
import logging

import yaml


logger = logging.getLogger(__name__)


def read_yaml(path: str) -> dict:
    res = None
    with open(path, 'r') as f:
        try:
            res = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.critical(f'Failed reading yaml from {path}: '
                            f'{type(e).__name__}: {e}')
    return res
