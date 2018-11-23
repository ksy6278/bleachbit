# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2018 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Cross-platform, special cleaning operations
"""
// 클래스 선언
from __future__ import absolute_import, print_function
from bleachbit.Options import options
from bleachbit import FileUtilities

//import문 선언
import os.path


// 구글 Chrome 또는 Chrominum의 history 버전을 가져오는 함수
// ‘path’는 같은 디렉토리에 있는 모든 파일이다.
def __get_chrome_history(path, fn='History'):
    path_history = os.path.join(os.path.dirname(path), fn)
    ver = get_sqlite_int(
        path_history, 'select value from meta where key="version"')[0]
    assert ver > 1
    return ver

// 문자열을 분할하는 SQL 명령 생성하는 함수
def __shred_sqlite_char_columns(table, cols=None, where=""):
     cmd = ""
    if cols and options.get('shred'):
        cmd += "update or ignore %s set %s %s;" % \
            (table, ",".join(["%s = randomblob(length(%s))" % (col, col)
                              for col in cols]), where)
        cmd += "update or ignore %s set %s %s;" % \
            (table, ",".join(["%s = zeroblob(length(%s))" % (col, col)
                              for col in cols]), where)
    cmd += "delete from %s %s;" % (table, where)
    return cmd

//SQLite 데이터베이스에 테이블 있는지 확인하는 함수
def __sqlite_table_exists(pathname, table):
    cmd = "select name from sqlite_master where type='table' and name=?;"
    import sqlite3
    conn = sqlite3.connect(pathname)
    cursor = conn.cursor()
    ret = False
    cursor.execute(cmd, (table,))
    if cursor.fetchone():
        ret = True
    cursor.close()
    conn.commit()
    conn.close()
    return ret

// path’의 데이터베이스에서 SQL을 실행하고 정수를 반환하는 함수
def get_sqlite_int(path, sql, parameters=None):
    ids = []
    import sqlite3
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    if parameters:
        cursor.execute(sql, parameters)
    else:
        cursor.execute(sql)
    for row in cursor:
        ids.append(int(row[0]))
    cursor.close()
    conn.close()
    return ids

// 구글 Chrominum / Chrome ‘Web Data’ 데이터베이스에서 자동 채우기 테이블 삭제 함수
def delete_chrome_autofill(path):
    cols = ('name', 'value', 'value_lower')
    cmds = __shred_sqlite_char_columns('autofill', cols)
    cols = ('first_name', 'middle_name', 'last_name', 'full_name')
    cmds += __shred_sqlite_char_columns('autofill_profile_names', cols)
    cmds += __shred_sqlite_char_columns('autofill_profile_emails', ('email',))
    cmds += __shred_sqlite_char_columns('autofill_profile_phones', ('number',))
    cols = ('company_name', 'street_address', 'dependent_locality',
            'city', 'state', 'zipcode', 'country_code')
    cmds += __shred_sqlite_char_columns('autofill_profiles', cols)
    cols = (
        'company_name', 'street_address', 'address_1', 'address_2', 'address_3', 'address_4',
        'postal_code', 'country_code', 'language_code', 'recipient_name', 'phone_number')
    cmds += __shred_sqlite_char_columns('server_addresses', cols)
    FileUtilities.execute_sqlite3(path, cmds)

// Database.db 파일로부터 HTML5 쿠키 삭제 함수
def delete_chrome_databases_db(path):
    cols = ('origin', 'name', 'description')
    where = "where origin not like 'chrome-%'"
    cmds = __shred_sqlite_char_columns('Databases', cols, where)
    FileUtilities.execute_sqlite3(path, cmds)

// 구글 Chrome / Chrominum에서 북마크 내역에 사용하지 않는 즐겨찾기 삭제 함수
def delete_chrome_favicons(path):
    path_history = os.path.join(os.path.dirname(path), 'History')
    ver = __get_chrome_history(path)
    cmds = ""

    if ver >= 4:
      
        // 아이콘 맵핑
        cols = ('page_url',)
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where page_url not in (select distinct url from History.urls)"
        cmds += __shred_sqlite_char_columns('icon_mapping', cols, where)

       // 이미지
        cols = ('image_data', )
        where = "where icon_id not in (select distinct icon_id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicon_bitmaps', cols, where)

        
        if ver < 28:
            cols = ('url', 'image_data')
        else:
            cols = ('url', )
        where = "where id not in (select distinct icon_id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    elif 3 == ver:
        
        cols = ('url', 'image_data')
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where id not in(select distinct favicon_id from History.urls)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    else:
        raise RuntimeError('%s is version %d' % (path, ver))

    FileUtilities.execute_sqlite3(path, cmds)

// 북마크에 영향을 주지 않고 기록 및 Favicon 파일의 기록 정리 함수
def delete_chrome_history(path):
    cols = ('url', 'title')
    where = ""
    ids_int = get_chrome_bookmark_ids(path)
    if ids_int:
        ids_str = ",".join([str(id0) for id0 in ids_int])
        where = "where id not in (%s) " % ids_str
    cmds = __shred_sqlite_char_columns('urls', cols, where)
    cmds += __shred_sqlite_char_columns('visits')
    cols = ('lower_term', 'term')
    cmds += __shred_sqlite_char_columns('keyword_search_terms', cols)
    ver = __get_chrome_history(path)
    if ver >= 20:

        if ver >= 28:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('current_path', 'target_path'))
            cmds += __shred_sqlite_char_columns(
                'downloads_url_chains', ('url', ))
        else:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('full_path', 'url'))
        cmds += __shred_sqlite_char_columns('segments', ('name',))
        cmds += __shred_sqlite_char_columns('segment_usage')
    FileUtilities.execute_sqlite3(path, cmds)

// 구글 Chrome / Chrominum 웹 데이터 데이터베이스에서 키워드 테이블 삭제 함수
def delete_chrome_keywords(path):
    cols = ('short_name', 'keyword', 'favicon_url',
            'originating_url', 'suggest_url')
    where = "where not date_created = 0"
    cmds = __shred_sqlite_char_columns('keywords', cols, where)
    cmds += "update keywords set usage_count = 0;"
    ver = __get_chrome_history(path, 'Web Data')
    if 43 <= ver < 49:
        cmds += __shred_sqlite_char_columns('keywords_backup', cols, where)
        cmds += "update keywords_backup set usage_count = 0;"

    FileUtilities.execute_sqlite3(path, cmds)

// 레지스트리 수정에서 LibreOffice 3.4 및 Apache MR 3.4 MRU를 지우는 함수
def delete_office_registrymodifications(path):
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    modified = False
    for node in dom1.getElementsByTagName("item"):
        if not node.hasAttribute("oor:path"):
            continue
        if not node.getAttribute("oor:path").startswith('/org.openoffice.Office.Histories/Histories/'):
            continue
        node.parentNode.removeChild(node)
        node.unlink()
        modified = True
    if modified:
        dom1.writexml(open(path, "w"))

// Mozilla place.sqlite URL 기록 삭제 함수
def delete_mozilla_url_history(path):

    cmds = ""

    // moz_place에 있는 URL 삭제
    places_suffix = "where id in (select " \
        "moz_places.id from moz_places " \
        "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
        "where moz_bookmarks.id is null); "

    cols = ('url', 'rev_host', 'title')
    cmds += __shred_sqlite_char_columns('moz_places', cols, places_suffix)

   
    //moz_annos에 있는 주석 삭제
    annos_suffix = "where id in (select moz_annos.id " \
        "from moz_annos " \
        "left join moz_places " \
        "on moz_annos.place_id = moz_places.id " \
        "where moz_places.id is null); "

    cmds += __shred_sqlite_char_columns(
        'moz_annos', ('content', ), annos_suffix)

    // favicons 삭제
    fav_suffix = "where id not in (select favicon_id " \
        "from moz_places where favicon_id is not null ); "

    if __sqlite_table_exists(path, 'moz_favicons'):
        cols = ('url', 'data')
        cmds += __shred_sqlite_char_columns('moz_favicons', cols, fav_suffix)

    // 방문 기록 삭제
    cmds += "delete from moz_historyvisits where place_id not " \
        "in (select id from moz_places where id is not null); "

    // input 기록 삭제
    input_suffix = "where place_id not in (select distinct id from moz_places)"
    cols = ('input', )
    cmds += __shred_sqlite_char_columns('moz_inputhistory', cols, input_suffix)

    // moz_hosts 전체 테이블 삭제
    if __sqlite_table_exists(path, 'moz_hosts'):
        cmds += __shred_sqlite_char_columns('moz_hosts', ('host',))
        cmds += "delete from moz_hosts;"

    // commend 실행
    FileUtilities.execute_sqlite3(path, cmds)

// OpenOffice.org MRU를 지우는 함수
def delete_ooo_history(path):
   
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    changed = False
    for node in dom1.getElementsByTagName("node"):
        if node.hasAttribute("oor:name"):
            if "History" == node.getAttribute("oor:name"):
                node.parentNode.removeChild(node)
                node.unlink()
                changed = True
                break
    if changed:
        dom1.writexml(open(path, "w"))

// 기록 파일의 경로를 지정하면 책갈피인 URL 테이블에서 ID를 반환 함수
def get_chrome_bookmark_ids(history_path):
    bookmark_path = os.path.join(os.path.dirname(history_path), 'Bookmarks')
    if not os.path.exists(bookmark_path):
        return []
    urls = get_chrome_bookmark_urls(bookmark_path)
    ids = []
    for url in urls:
        ids += get_sqlite_int(
            history_path, 'select id from urls where url=?', (url,))
    return ids

// 구글 Chrome / Chrominum의 책갈피인 URL 목록 반환함수
def get_chrome_bookmark_urls(path):
    """Return a list of bookmarked URLs in Google Chrome/Chromium"""
    import json

   // parser로 파일 읽어옴
    js = json.load(open(path, 'r'))

    // 빈 배열 선언
    urls = []
    
    // 지역 재귀함수 선언
    def get_chrome_bookmark_urls_helper(node):
        if not isinstance(node, dict):
            return
        if 'type' not in node:
            return
        if node['type'] == "folder":
            
            for child in node['children']:
                get_chrome_bookmark_urls_helper(child)
        if node['type'] == "url" and 'url' in node:
            urls.append(node['url'])

    // 북마크 찾는다
    for node in js['roots']:
        get_chrome_bookmark_urls_helper(js['roots'][node])

    return list(set(urls))
