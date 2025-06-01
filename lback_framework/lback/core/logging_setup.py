import logging
import logging.config

from .config import Config

def setup_logging(config: Config):
    if config.DEBUG:
        effective_level_str = getattr(config, "LOGGING_LEVEL", "INFO").upper()
    else:
        effective_level_str = "WARNING"

    effective_level = getattr(logging, effective_level_str, logging.INFO)

    log_config = getattr(config, "LOGGING", None)

    if log_config:
        try:
            if 'handlers' in log_config and 'console' in log_config['handlers']:
                log_config['handlers']['console']['level'] = logging.getLevelName(effective_level)
            
            if 'root' in log_config:
                 log_config['root']['level'] = logging.getLevelName(effective_level)
            elif '' in log_config.get('loggers', {}):
                 log_config['loggers']['']['level'] = logging.getLevelName(effective_level)
            
            logging.config.dictConfig(log_config)
            
            actual_effective_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
            logging.info(f"Logging configured using dictConfig. Effective level: {actual_effective_level}")


        except Exception as e:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            logging.error(f"Failed to configure logging using dictConfig: {e}. Falling back to basic config.")
            logging.info(f"Falling back to basic config. Effective level: {logging.getLevelName(logging.getLogger().getEffectiveLevel())}")

    else:
        logging.basicConfig(
            level=effective_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.info(f"LOGGING config not found. Logging configured using basicConfig with level: {effective_level_str}")