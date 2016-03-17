from pip.req import parse_requirements
import logging
import uuid

from argh import arg, dispatch_commands
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@arg('path', help='Path to check (directory or concrete file)')
def check(path):
    logger.info('Checking "%s"', path)

    for requirement in parse_requirements(path, session=uuid.uuid1()):
        url = 'https://pypi.python.org/pypi/%s/json' % requirement.name
        response = requests.get(url)

        if not response.ok:
            logging.error('Request to %s failed (%d)', url,
                          response.status_code)
            continue

        info = response.json()
        import json
        #logging.info(json.dumps(info, indent=2))
        logging.info('%s: %s', requirement.name, info['releases'].keys())


def main():
    dispatch_commands([check])


if __name__ == '__main__':
    main()
