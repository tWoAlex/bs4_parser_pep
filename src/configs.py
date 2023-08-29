import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR

LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument('mode', choices=available_modes,
                        help='Режимы работы парсера')
    parser.add_argument('-c', '--clear-cache', action='store_true',
                        default=False, help='Очистка кеша')
    parser.add_argument('-o', '--output', choices=('pretty', 'file'),
                        help='Дополнительные способы вывода данных')
    return parser


def configure_logging():
    log_dir = BASE_DIR.joinpath('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir.joinpath('parser.log')

    rotating_handler = RotatingFileHandler(log_file, encoding='utf-8',
                                           maxBytes=2 ** 20, backupCount=5,)
    logging.basicConfig(datefmt=DATETIME_FORMAT, format=LOG_FORMAT,
                        handlers=(rotating_handler, logging.StreamHandler()),
                        level=logging.INFO)
