from pip._vendor.packaging.version import Version, InvalidVersion
from pip.req import parse_requirements
import logging
import uuid

from argh import arg, dispatch_commands
import requests


logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def is_update(requirement, version):
    """
    :rtype: bool
    """
    for spec in requirement.specifier:
        if spec.operator == '==':
            if spec._get_operator('<=')(version, spec.version):
                return False
        elif spec.operator == '!=':
            if spec.version == release:
                return False
        elif spec.operator == '>':
            if spec._get_operator('<=')(version, spec.version):
                return False
        elif spec.operator == '>=':
            if spec._get_operator('<')(version, spec.version):
                return False
        elif spec.operator == '<':
            if spec._get_operator('<')(version, spec.version):
                return False
        elif spec.operator == '<=':
            if spec._get_operator('<=')(version, spec.version):
                return False
        else:
            raise ValueError('Unknown operator: %s' % spec.operator)

    return True


@arg('--pre-releases', help='Show pre-releases (alpha, beta etc.)')
@arg('path', help='Path to check (directory or concrete file)')
def check(path, pre_releases=False):
    logger.info('Checking "%s"', path)

    for requirement in parse_requirements(path, session=uuid.uuid1()):
        url = 'https://pypi.python.org/pypi/%s/json' % requirement.name
        response = requests.get(url)

        if not response.ok:
            logging.error('Request to %s failed (%d)', url,
                          response.status_code)
            continue

        info = response.json()
        updates = []

        for version in info['releases'].keys():
            try:
                version = Version(version)
            except InvalidVersion:
                # ==0.1dev-r1716' is f.ex. not parsed correctly.
                continue

            if not pre_releases and version.is_prerelease:
                continue

            if is_update(requirement, version):
                updates.append(str(version))

        if updates:
            logger.info('%s updates available: %s', requirement.name, updates)

def main():
    dispatch_commands([check])


if __name__ == '__main__':
    main()
