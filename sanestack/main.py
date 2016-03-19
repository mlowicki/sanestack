from pip.download import PipSession
from pip.index import PackageFinder
from pip._vendor.packaging.version import (
    InvalidVersion,
    LegacyVersion,
    Version,
    parse,
)
from pip.req import parse_requirements
from tempfile import NamedTemporaryFile
import logging

from argh import arg, dispatch_command
from argh.exceptions import CommandError
import colorlog
import requests

from sanestack import __version__


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
        spec_version = Version(spec.version)

        if spec.operator == '==':
            if version <= spec_version:
                return False
        elif spec.operator == '!=':
            if version == spec_version:
                return False
        elif spec.operator == '>':
            if version <= spec_version:
                return False
        elif spec.operator == '>=':
            if version < spec_version:
                return False
        elif spec.operator == '<':
            if version < spec_version:
                return False
        elif spec.operator == '<=':
            if version <= spec_version:
                return False
        else:
            raise ValueError('Unknown operator: %s' % spec.operator)

    return True


def get_updates(requirement, legacy_versions, pre_releases):
    """
    Get all updates for passed requirement.
    :param requirement:
    :type: pip.req.req_install.InstallRequirement
    :param legacy_versions: allow legacy versions (f.ex. 0.1dev-r1716')
    :type: bool
    :param pre_releases: allow pre-releases (beta, alpha etc.)
    :type: bool
    :rtype: list(str)
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

    return updates


def get_requirements(path, line):
    """
    :param path: path to requirements file
    :type: str
    :param line: single requirements line (f.ex. "ipdb=0.0.1")
    :type: str
    :rtype: list(pip.req.req_install.InstallRequirement)
    """
    session = PipSession()
    finder = PackageFinder(find_links=[], index_urls=[], session=session)

    if path is not None:
        for requirement in parse_requirements(path, session=session,
                                              finder=finder):
            yield requirement

    if line is not None:
        with NamedTemporaryFile() as f:
            f.write(line)
            f.seek(0)

            for requirement in parse_requirements(f.name, session=session,
                                                  finder=finder):
                yield requirement


@arg('-V', '--version', help='Print version')
@arg('-l', '--line', help='requirements line to check (f.ex. "ipdb=0.0.1")')
@arg('--skip-packages', help='list of packages to skip checking',
     nargs='+', type=str, metavar='PACKAGE')
@arg('--packages', help='list of packages to check',
     nargs='+', type=str, metavar='PACKAGE')
@arg('-v', '--verbose', help='verbose mode')
@arg('--legacy-versions', help='show legacy versions')
@arg('--pre-releases', help='show pre-releases (alpha, beta etc.)')
@arg('path', help='requirements file to check', nargs='?')
def check(path, pre_releases=False, legacy_versions=False, verbose=False,
          packages=[], skip_packages=[], line=None, version=False):
    setup_logging(verbose)

    if version:
        logger.info(__version__)
        return

    if line is None and path is None:
        raise CommandError('at least one of path or line is required')

    total_updates = 0

    for requirement in get_requirements(path, line):
        if ((packages and requirement.name not in packages) or
            (skip_packages and requirement.name in skip_packages) or
            requirement.editable):
            continue

        if len(requirement.specifier) == 0:
            logger.warn('Version of %s not locked', requirement.name)
            continue

        updates = get_updates(requirement=requirement,
                              legacy_versions=legacy_versions,
                              pre_releases=pre_releases)

        if not updates:
            continue

        logger.info('Updates for %s found: %s', requirement.name,
                    [str(version) for version in sorted(updates)])
        total_updates += len(updates)

    logger.info('%d updates found', total_updates)


def main():
    dispatch_command(check)


if __name__ == '__main__':
    main()
