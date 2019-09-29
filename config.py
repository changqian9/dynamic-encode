import os, sys

DEBUG = bool(os.environ.get('DEBUG', 1))
EXIT_STATUS_FILE = os.path.abspath(os.environ.get('EXIT_STATUS_FILE', '/airflow/xcom/return.json'))
LOG_DIR = os.environ.get('LOG_DIR', os.getcwd())

LOG_SUFFIX = os.environ.get('LOG_SUFFIX', "")
APP_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]
LOG = {
    'file_name': os.environ.get('LOG_FILE_NAME', APP_NAME + LOG_SUFFIX + ".log"),
    'file_size': int(os.environ.get('LOG_FILE_SIZE', 100 * 1024 * 1024)),
    'backup_count': 10
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose_more': {
            'format': "%(asctime)s %(pathname)s:%(funcName)s[%(lineno)d] %(levelname)s>%(message)s",
        },
        'verbose': {
            'format': "%(asctime)s %(filename)s:%(funcName)s[%(lineno)d] %(levelname)s>%(message)s",
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'handlers': {
        'file_extensive': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose_more',
            'filename': os.path.join(LOG_DIR, LOG['file_name']),
            'maxBytes': LOG['file_size'],
            'backupCount': LOG['backup_count'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_DIR, LOG['file_name']),
            'maxBytes': LOG['file_size'],
            'backupCount': LOG['backup_count'],
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'simple': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        'extensive_file_only': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['file_extensive']
        },
        'extensive_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['file_extensive', 'console']
        },
        'verbose_file_only': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['file']
        },
        'verbose_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['file', 'console']
        },
        'extensive': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['console']
        },
        'verbose': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['simple']
        }
    },
}

_LOGGER_NAME = os.environ.get('LOGGER', 'extensive')

LOGGER_NAME = _LOGGER_NAME if _LOGGER_NAME in LOGGING['loggers'] else 'extensive'
