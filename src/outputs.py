import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


def control_output(results, cli_args):
    output = cli_args.output

    if output == 'pretty':
        pretty_output(results)
    elif output == 'file':
        file_output(results, cli_args)
    else:
        default_output(results)


def default_output(results):
    print(*results, sep='\n')


def pretty_output(results):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'

    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR.joinpath('results')
    results_dir.mkdir(exist_ok=True)

    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    filename = f'{cli_args.mode}_{now_formatted}.csv'
    filepath = results_dir.joinpath(filename)

    with open(filepath, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='unix',)
        writer.writerows(results)
        logging.info(f'Файл с результатами был сохранён: {filepath}')
