import logging
from os.path import isfile
from .cli import FloopCLI

logger = logging.getLogger(__name__)

def main() -> None:
    import logging.config
    import yaml

    path = './floop/log.yaml'
    if isfile(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    FloopCLI()
