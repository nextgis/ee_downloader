__author__ = "Dmitry Barishnikov (dmitry.baryshnikov@nextgis.ru), Dmitry Kolesov (kolesov.dm@gmail.com)"
__copyright__ = "Copyright (C) NextGIS"
__license__ = "GPL v.2"

import os
import requests
import json
import time
import tempfile
import shutil
import re

from bs4 import BeautifulSoup

from utils import check_archive_fast, silent_remove
import credentials as creds
import config as downloader_config


def get_session_id(s, login, password):
    response = s.get(downloader_config.AUTH_URL)
    match = re.search(r'value="(.*?)" id="csrf_token"', response.content)
    csrf_token = match.group(1)

    payload = {'username': login, 'password': password, 'csrf_token': csrf_token}
    response = s.post(downloader_config.AUTH_URL, data=payload, allow_redirects=False)

    if response.status_code != 302:
        raise RuntimeError('Authentication Failed')


def set_empty_filter(session):
    payload = {
        'tab': 1,
        'destination': 2,
        'coordinates': [],
        'format': 'dms',
        'dStart': '',
        'dEnd': '',
        'searchType': 'Std',
        'includeUnknownCC': 1,
        'num': str(downloader_config.MAX_SCENE_COUNT),
        'months': ['', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'],
        'pType': 'polygon'
    }

    _ = session.post(downloader_config.EE_URL + '/tabs/save', data={'data': json.dumps(payload)})


def set_dataset(session, dataset_id):
    payload = {
        'tab': 2,
        'destination': 3,
        'cList': [dataset_id],
        'selected': dataset_id
    }

    _ = session.post(downloader_config.EE_URL + '/tabs/save', data={'data': json.dumps(payload)})


def set_dataset_additional_criteria(session, dataset_id, identifiers, product_name):
    if not identifiers:
        identifiers = []

    field_identifier_ids = downloader_config.PRODUCTS[product_name]['field_identifier_ids']

    if len(identifiers) > len(field_identifier_ids):
        raise Exception('Count of identifiers is to many. Max count of identifiers is {0}'
                        .format(len(field_identifier_ids)))

    filter_by_identifiers = dict()
    for i, identifier in enumerate(identifiers):
        filter_by_identifiers[field_identifier_ids[i]] = identifier

    filter_by_selects = {select_id: [''] for select_id in
                         downloader_config.PRODUCTS[product_name]['select_ids']}

    filters = dict(filter_by_identifiers.items() + filter_by_selects.items())

    payload = {
        'tab': 3,
        'destination': 4,
        'criteria': {
            dataset_id: filters
        },
        'selected': dataset_id}

    params = dict()
    params["data"] = json.dumps(payload)

    _ = session.post(downloader_config.EE_URL + '/tabs/save', data=params)


def fill_metadata(session, scene):
    req = session.get(scene['metadata'])

    soup = BeautifulSoup(req.text, 'html.parser')
    for tr in soup.find_all('tr'):
        if tr.td is not None:
            scene[tr.td.a.string] = tr.td.next_sibling.next_sibling.string


def fill_download_options(session, scene, product_name):
    product_id = str(downloader_config.PRODUCTS[product_name]['id'])
    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    req = session.get(downloader_config.EE_URL + '/download/options/' + product_id + '/' + scene['id'], headers=headers)

    soup = BeautifulSoup(req.text, 'html.parser')
    for input in soup.find_all('input'):
        onclick = input['onclick']
        onclick = onclick.replace("'", "")
        onclick = onclick.replace("window.location=", "")
        if 'disabled' in input.attrs:
            print 'Skip download URL ' + onclick
        else:
            scene[unicode.strip(input.findNext('div').text)] = onclick


def download_scene(scene, login, password, result_dir, tmp_path, product_name, product_format):
    """
    Download Landsat Scene. Return result filename or None if the scene can't be downloaded.

    :param scene:   Scene
    :param login:   login
    :param password:    password
    :param result_dir:  directory for store the scene archive
    :param tmp_path:  temporary directory for store the scene archive
    :param product_name:  name of the product from config (e.g. 'Landsat 8 OLI/TIRS C1 Level-1' or 'Sentinel-2')
    :return:    path to the archive or None if an error occurs
    """
    scene_identifier_key = downloader_config.PRODUCTS[product_name]['scene_identifier_key']
    scene_id = scene[scene_identifier_key]
    filename = os.path.join(result_dir,
                            '{name}{extension}'.format(name=scene_id,
                                                       extension=downloader_config.FORMATS[product_format][
                                                           'extension']))
    if os.path.isfile(filename):
        return filename

    data_format_keys = [key for key in scene.keys() if product_format in key]

    if data_format_keys:
        data_format_key = data_format_keys[0]
    else:
        print 'Format "{format}" is unavailable for scene "{scene_id}"'.format(format=product_format,
                                                                               scene_id=scene_id)
        return None

    if scene[data_format_key]:
        download_url = scene[data_format_key]
        tmp_scene_file = tempfile.mktemp(dir=tmp_path) + \
                         downloader_config.FORMATS[product_format]['extension']
        try:
            _download_file(login, password, download_url, tmp_scene_file)
        except Exception:
            print 'ERROR: Failed download "{format}" for scene "{scene_id}"' \
                .format(format=product_format, scene_id=scene_id)
            return None
        finally:
            if os.path.isfile(tmp_scene_file):
                shutil.move(tmp_scene_file, filename)
            print 'File "{file_name}" is downloaded'.format(file_name=filename)
    else:
        print 'ERROR: No url for "{format}" for scene "{scene_id}"' \
            .format(format=product_format, scene_id=scene_id)
        return None

    if check_archive_fast(filename, product_format):
         scene['downloaded'] = True
         print 'File "{file_name}" is checked successfully'.format(file_name=filename)
         return filename
    else:
         print 'Downloaded file "{file_name}" is broken. The file will be removed.'.format(file_name=filename)
         silent_remove(filename)
         return None 

def get_scenes(login, password, identifiers, product_name):
    product_id = str(downloader_config.PRODUCTS[product_name]['id'])

    session = requests.session()
    get_session_id(session, login, password)
    set_empty_filter(session)
    set_dataset(session, product_id)
    set_dataset_additional_criteria(session, product_id, identifiers, product_name)

    req = session.get('{url}/result/count?collection_id={product_id}&_={time}'
                      .format(url=downloader_config.EE_URL, product_id=product_id, time=str(int(time.time() * 1000))))
    dictionary = req.json()

    scenes_count = int(dictionary.get('collectionCount'))
    print 'Received ' + dictionary.get('collectionCount') + ' scenes'

    if scenes_count == 0:
        return
    elif scenes_count > downloader_config.MAX_SCENE_COUNT:
        raise RuntimeError('Too mach scenes. Modify search criteria')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': downloader_config.EE_URL,
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }

    req = session.post(downloader_config.EE_URL + '/result/index', data='collectionId=' + product_id, headers=headers)

    soup = BeautifulSoup(req.text, 'html.parser')

    scene_list = []

    for imgtag in soup.find_all('img'):
        id = imgtag['class']
        if id is not None:
            scene = dict()
            scene['id'] = id[0]
            scene['preview'] = imgtag['src'].replace('/browse/thumbnails/', '/browse/')
            scene['metadata'] = downloader_config.EE_URL + '/form/metadatalookup/?collection_id=' + \
                                product_id + '&entity_id=' + scene['id']
            scene_list.append(scene)

    for scene in scene_list:
        fill_metadata(session, scene)
        fill_download_options(session, scene, product_name)

    return scene_list


def _download_file(login, password, url, filename):
    session = requests.session()
    get_session_id(session, login, password)
    r = session.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def download_scenes_by_ids(login, password, identifiers, temp_dir, product_name, product_format, result_dir=None):
    """
    Download Scene by identifiers. Return result array of scenes info.

    :param login:   login
    :param password:    password
    :param identifiers: array of scene identifiers
    :param temp_dir:  temporary directory for store the scene archive
    :param product_name:  name of the product from config (e.g. 'Landsat 8 OLI/TIRS C1 Level-1' or 'Sentinel-2')
    :param product_format:  file format name from config (e.g. 'Level-1 GeoTIFF Data Product' or 'LandsatLook Quality Image')
    :param result_dir:  directory for store the scene archive
    :return:    array of scenes info
    """
    if not login:
        raise ValueError('Login should be no empty')
    if not password:
        raise ValueError('Password should be no empty')
    if product_name not in downloader_config.PRODUCTS:
        raise ValueError('Product "{0}" is not defined into config.py'.format(product_name))
    if product_format not in downloader_config.FORMATS:
        raise ValueError('Format "{0}" is not defined into config.py'.format(product_format))
    if not type(identifiers) is list:
        raise ValueError('Identifiers should be a list')
    if not identifiers:
        raise ValueError('Identifiers should be no empty list')

    current_result_dir = result_dir if result_dir else temp_dir

    scenes_info = get_scenes(login=login, password=password, identifiers=identifiers, product_name=product_name)

    if scenes_info is None:
        return []

    for scene_info in scenes_info:
        filename = download_scene(scene_info, login, password, current_result_dir, temp_dir, product_name,
                                  product_format)
        scene_info['file_name'] = filename
        print scene_info

    return scenes_info


if __name__ == "__main__":
    login = creds.login
    password = creds.password

    product_name = 'Sentinel-2'
    product_format = 'Full Resolution Browse in GeoTIFF format'

    scenes = get_scenes(login=login,
                        password=password,
                        identifiers=[
                            'S2A_OPER_MSI_L1C_TL_SGS__20160716T080034_20160716T113445_A005566_T39UWB_N02_04_01'],
                        product_name=product_name)

    for s in scenes:
        print s
        download_scene(s, login, password, '/tmp/', '/tmp', product_name, product_format)
