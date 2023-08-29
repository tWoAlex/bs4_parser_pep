import re
import logging
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, PEPS_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_with_python = div_with_ul.find_all('li',
                                                attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
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


def latest_versions(session):
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


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    downloads_dir = BASE_DIR.joinpath('downloads')
    response = get_response(session, downloads_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})

    link = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = link.split(sep='/')[-1]
    downloads_dir.mkdir(exist_ok=True)
    filepath = downloads_dir.joinpath(filename)

    response = session.get(link)
    with open(filepath, 'wb') as file:
        file.write(response.content)
        logging.info(f'Архив был загружен и сохранён: {filepath}')


def pep(session):
    def parse_section(soup: BeautifulSoup, header_tag) -> tuple[str, list]:
        """Возвращает кортеж вида (Заголовок таблицы, список PEPов),
        где каждый PEP из списка — кортеж вида
        (номер, ссылка, тип и статус, название, авторы)."""
        header = find_tag(soup, header_tag)
        table_rows = find_tag(soup, 'tbody')

        peps = []
        for row in table_rows.find_all('tr'):
            type_n_status, number, title, authors = row.find_all('td')
            href = urljoin(PEPS_URL, find_tag(row, 'a')['href'])
            peps.append(
                (int(number.text), href,
                 type_n_status.text, title.text, authors.text)
            )
        return header.text, peps

    def status_from_pep_soup(soup: BeautifulSoup):
        """Возвращает статус со страницы PEPа."""
        table = find_tag(soup, 'dl',
                         attrs={'class': 'rfc2822 field-list simple'})
        lines = zip(table.find_all('dt'), table.find_all('dd'))

        pep_status = None
        for dt_tag, dd_tag in lines:
            if dt_tag.text == 'Status:':
                pep_status = dd_tag.text

        return pep_status

    response = get_response(session, PEPS_URL)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    numerical_index = find_tag(soup, 'section',
                               attrs={'id': 'numerical-index'})
    numerical_index = parse_section(numerical_index, 'h2')

    pep_statuses = dict()
    status_conflicts = []
    for _, url, ts, _, _ in tqdm(numerical_index[1],
                                 leave=False, unit=' PEP',
                                 desc='Получение данных со страницы PEPa'):
        pep_page = get_response(session, url).text
        pep_page = BeautifulSoup(pep_page, features='lxml')

        table_statuses = EXPECTED_STATUS[ts[1:]]
        pep_status = status_from_pep_soup(pep_page)

        if pep_status not in table_statuses:
            status_conflicts.append(
                (f'{url}\nСтатус в карточке: {pep_status}'
                 f'\nОжидаемые статусы: {table_statuses}')
            )

        pep_statuses[pep_status] = (pep_statuses[pep_status] + 1
                                    if pep_status in pep_statuses else 1)

    if status_conflicts:
        logging.warning(
            '\nНесовпадающие статусы:\n'
            '\n'.join(status_conflicts)
        )

    pep_statuses = sorted(pep_statuses.items())
    pep_statuses = (
        [('Статус', 'Количество')]
        + pep_statuses +
        [('Total', sum(map(lambda x: x[1], pep_statuses)))]
    )
    return pep_statuses


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results:
        control_output(results, args)

    logging.info('Парсер завершил свою работу')


if __name__ == '__main__':
    main()
