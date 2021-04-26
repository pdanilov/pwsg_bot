def setup():
    from loguru import logger
    logger.info('Configure handlers')

    from . import common
    from . import add
    from . import list
    from . import reset
