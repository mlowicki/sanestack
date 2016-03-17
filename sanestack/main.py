import logging

from argh import arg, dispatch_commands


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@arg('path', help='Path to check (directory or concrete file)')
def check(path):
    logger.info('Checking "%s"', path)


def main():
    dispatch_commands([check])


if __name__ == '__main__':
    main()
