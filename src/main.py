import re
import logging
from pathlib import Path
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new():
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    session = requests_cache.CachedSession()
    response = get_response(session, whats_new_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_with_python = div_with_ul.find_all('li',
                                                attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_with_python, desc='Секции', unit='секц.'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']

        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if not response:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl_text = find_tag(soup, 'dl').text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_version():
    session = requests_cache.CachedSession()
    response = get_response(session, MAIN_DOC_URL)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for tag in tqdm(a_tags, desc='Версии', unit='верс.'):
        link = tag['href']
        text_match = re.search(pattern, tag.text)
        if text_match:
            version, status = text_match.groups()
        else:
            version, status = tag.text, ''
        results.append((link, version, status))
    return results


def download():
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    downloads_dir = Path.joinpath(BASE_DIR, 'downloads')

    session = requests_cache.CachedSession()
    response = get_response(session, downloads_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})

    link = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = link.split(sep='/')[-1]
    downloads_dir.mkdir(exist_ok=True)
    filepath = Path.joinpath(downloads_dir, filename)

    response = session.get(link)
    with open(filepath, 'wb') as file:
        file.write(response.content)
        logging.info(f'Архив был загружен и сохранён: {filepath}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-version': latest_version,
    'download': download,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode]()
    if results:
        control_output(results, args)


if __name__ == '__main__':
    main()
