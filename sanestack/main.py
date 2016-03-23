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
from urlparse import urljoin
import logging
import re

from argh import arg, dispatch_command
from argh.exceptions import CommandError
import colorlog
import requests

from sanestack import __version__


logger = logging.getLogger(__name__)
DEFAULT_INDEX = 'https://pypi.python.org/pypi/'


def setup_logging(verbose):
    """
    Install logging facility.
    :param verbose: enable verbose logging
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
    logging.getLogger().addHandler(handler)
    handler.setFormatter(formatter)


def is_update(requirement, version):
    """
    Check if version is newer than version(s) specified by requirement's
    specifiers.
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


def get_versions_from_pypi(url):
    """
    Get list of versions for package from PyPI server.
    :param url: package url
    :type: str
    :rtype: list
    """
    response = requests.get(url)

    if not response.ok:
        return []

    payload = response.json()
    return payload['releases'].keys()


def get_versions_from_devpi(url):
    """
    Get list of versions for package from devpi server.
    :param url: package url
    :type: str
    :rtype: list
    """
    response = requests.get(url, headers={'Accept': 'application/json'})

    if not response.ok:
        return []

    payload = response.json()
    return payload['result'].keys()


def get_versions(package, index_urls):
    """
    Get packages' versions from supplied indices or default index if list of
    indices is empty.
    :param package: str
    :index_urls: list
    :rtype: set
    """
    if not index_urls:
        index_urls = [DEFAULT_INDEX]

    versions = set()

    for index_url in index_urls:
        if index_url.endswith('+simple/'):
            package_url = re.sub(r'\+simple/', package, index_url)
            versions.update(get_versions_from_devpi(package_url))
        else:
            package_url = urljoin(index_url, '%s/json' % package)
            versions.update(get_versions_from_pypi(package_url))

    return versions


def get_updates(requirement, legacy_versions, pre_releases, index_urls):
    """
    Get all updates for passed requirement.
    :param requirement:
    :type: pip.req.req_install.InstallRequirement
    :param legacy_versions: allow legacy versions (f.ex. 0.1dev-r1716')
    :type: bool
    :param pre_releases: allow pre-releases (beta, alpha etc.)
    :type: bool
    :param index_urls: urls of indices
    :type: list
    :rtype: list(str)
    """
    versions = get_versions(requirement.name, index_urls)

    if not versions:
        logger.error('No versions found for %s', requirement.name)
        return []

    updates = []

    for version in versions:
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


def get_requirements(path, line, session, finder):
    """
    :param path: path to requirements file
    :type: str
    :param line: single requirements line (f.ex. "ipdb=0.0.1")
    :type: str
    :param session:
    :type: pip.download.PipSession
    :param finder:
    :type: pip.index.PackageFinder
    :rtype: list(pip.req.req_install.InstallRequirement)
    """
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


def is_version_locked(requirement):
    """
    Check if requirement's specifers lock package to single version
    (f.ex. "django==1.7.0") or bounded range (f.ex "django>=1.7,<1.8").
    :param requirement:
    :type: pip.req.req_install.InstallRequirement
    :rtype: bool
    """
    for spec in requirement.specifier:
        if spec.operator in ('==', '<', '<='):
            return True

    return False


@arg('-V', '--version', help='Print version')
@arg('-l', '--line', help='requirements line to check (f.ex. "ipdb=0.0.1")')
@arg('--skip-packages', help='list of packages to skip checking',
     nargs='+', type=str, metavar='PACKAGE')
@arg('--packages', help='list of packages to check',
     nargs='+', type=str, metavar='PACKAGE')
@arg('-v', '--verbose', help='verbose mode')
@arg('--legacy-versions', help='show legacy versions')
@arg('--pre-releases', help='show pre-releases (alpha, beta etc.)')
@arg('path', help='path or url of requirements file', nargs='?')
def check(path, pre_releases=False, legacy_versions=False, verbose=False,
          packages=[], skip_packages=[], line=None, version=False):
    setup_logging(verbose)

    if version:
        logger.info(__version__)
        return

    if line is None and path is None:
        raise CommandError('at least one of path or line is required')

    total_updates = 0

    session = PipSession()
    finder = PackageFinder(find_links=[], index_urls=[], session=session)

    for requirement in get_requirements(path, line, session, finder):
        if ((packages and requirement.name not in packages) or
            (skip_packages and requirement.name in skip_packages) or
            requirement.editable):
            continue

        if not is_version_locked(requirement):
            logger.warn('Version of %s not locked', requirement.name)
            continue

        updates = get_updates(requirement=requirement,
                              legacy_versions=legacy_versions,
                              pre_releases=pre_releases,
                              index_urls=finder.index_urls)

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
