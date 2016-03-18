from pip.download import PipSession
from pip.index import PackageFinder
from pip._vendor.packaging.version import (
    InvalidVersion,
    LegacyVersion,
    parse,
)
from pip.req import parse_requirements
import logging

from argh import arg, dispatch_commands
import colorlog
import requests


logger = logging.getLogger(__name__)


def setup_logging(verbose):
    """
    :param verbose: Enable verbose logging
    :type: bool
    """
    if verbose:
        logging.getLogger('requests').setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)s:%(name)s:%(message)s')
    else:
        logging.getLogger('requests').setLevel(logging.WARNING)
        logger.setLevel(logging.INFO)
        formatter = colorlog.ColoredFormatter('%(log_color)s%(message)s')

    handler = logging.StreamHandler()
    logging.getLogger('').addHandler(handler)
    handler.setFormatter(formatter)


def is_update(requirement, version):
    """
    :param requirement:
    :type: pip.req.req_install.InstallRequirement
    :param version:
    :type: pip._vendor.packaging.version.Version
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


def find_updates(requirement, legacy_versions, pre_releases):
    """
    Find all updates for passed requirement.
    :param requirement:
    :type: pip.req.req_install.InstallRequirement
    :param legacy_versions: allow legacy versions (f.ex. 0.1dev-r1716')
    :type: bool
    :param pre_releases: allow pre-releases (beta, alpha etc.)
    :type: bool
    """
    url = 'https://pypi.python.org/pypi/%s/json' % requirement.name
    response = requests.get(url)

    if not response.ok:
        logger.error('Request to %s failed (%d)', url,
                      response.status_code)
        return

    info = response.json()
    updates = []

    for version in info['releases'].keys():
        try:
            version = parse(version)
        except InvalidVersion:
            logger.error('Cannot parse version: %s', version)
            continue

        if not legacy_versions and isinstance(version, LegacyVersion):
            continue

        if not pre_releases and version.is_prerelease:
            continue

        if is_update(requirement, version):
            updates.append(version)

    if updates:
        logger.info('Updates for %s available: %s', requirement.name,
                    [str(version) for version in sorted(updates)])


@arg('--packages', help='List of packages to check. All if not set',
     nargs='+', type=str)
@arg('-v', '--verbose', help='Verbose mode')
@arg('--legacy-versions', help='Show legacy versions')
@arg('--pre-releases', help='Show pre-releases (alpha, beta etc.)')
@arg('path', help='Path to check (directory or concrete file)')
def check(path, pre_releases=False, legacy_versions=False, verbose=False,
          packages=[]):
    setup_logging(verbose)
    logger.info('Checking "%s"', path)
    session = PipSession()
    finder = PackageFinder(find_links=[], index_urls=[], session=session)

    for requirement in parse_requirements(path, session=session,
                                          finder=finder):
        if packages and requirement.name not in packages:
            continue

        find_updates(requirement=requirement,
                     legacy_versions=legacy_versions,
                     pre_releases=pre_releases)


def main():
    dispatch_commands([check])


if __name__ == '__main__':
    main()
