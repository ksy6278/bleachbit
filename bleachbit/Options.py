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
Store and retrieve user preferences
"""

//클래스 선언
from __future__ import absolute_import, print_function
from bleachbit import General

// import문 선언
import bleachbit
import logging
import os
import re
import traceback

logger = logging.getLogger(__name__)

if 'nt' == os.name:
    from win32file import GetLongPathName


boolean_keys = ['auto_hide', 'auto_start', 'check_beta',
                'check_online_updates', 'first_start', 'shred', 'exit_done', 'delete_confirmation', 'units_iec']
if 'nt' == os.name:
    boolean_keys.append('update_winapp2')

// 경로 이름을 .ini 옵션 이름으로 변경 함수
def path_to_option(pathname):
   
    pathname = os.path.normcase(pathname)
    
    if 'nt' == os.name and os.path.exists(pathname):
        pathname = GetLongPathName(pathname)
    if ':' == pathname[1]:
       
        pathname = pathname[0] + pathname[2:]
    return pathname

// 사용자 기본 설정 저장 및 검색 클래스
class Options:

    // 초기화 함수
    def __init__(self):
        self.purged = False
        self.config = bleachbit.RawConfigParser()
        self.config.optionxform = str  # make keys case sensitive for hashpath purging
        self.config._boolean_states['t'] = True
        self.config._boolean_states['f'] = False
        self.restore()

     // 디스크에 정보 쓰는 함수
    def __flush(self):
       
        if not self.purged:
            self.__purge()
        if not os.path.exists(bleachbit.options_dir):
            General.makedirs(bleachbit.options_dir)
        mkfile = not os.path.exists(bleachbit.options_file)
        _file = open(bleachbit.options_file, 'wb')
        try:
            self.config.write(_file)
        except IOError as e:
            print(e)
            from errno import ENOSPC
            if e.errno == ENOSPC:
                logger.error("disk is full writing configuration '%s'", bleachbit.options_file)
            else:
                raise
        if mkfile and General.sudo_mode():
            General.chownself(bleachbit.options_file)

    // 사용되지 않는 데이터 지우는 함수        
    def __purge(self):
        
        self.purged = True
        if not self.config.has_section('hashpath'):
            return
        for option in self.config.options('hashpath'):
            pathname = option
            if 'nt' == os.name and re.search('^[a-z]\\\\', option):
                # restore colon lost because ConfigParser treats colon special
                # in keys
                pathname = pathname[0] + ':' + pathname[1:]
                pathname = pathname.decode('utf-8')
            exists = False
            try:
                exists = os.path.lexists(pathname)
            except:
                # this deals with corrupt keys
                # https://www.bleachbit.org/forum/bleachbit-wont-launch-error-startup
                logger.error('error checking whether path exists: %s ', pathname)
            if not exists:
                # the file does not on exist, so forget it
                self.config.remove_option('hashpath', option)
    // 기본 값 설정 함수
    def __set_default(self, key, value):
       
        if not self.config.has_option('bleachbit', key):
            self.set(key, value)

    // 일반 옵션 검색 함수
    def get(self, option, section='bleachbit'):
        
        if not 'nt' == os.name and 'update_winapp2' == option:
            return False
        if section == 'hashpath' and option[1] == ':':
            option = option[0] + option[2:]
        if option in boolean_keys:
            return self.config.getboolean(section, option)
        return self.config.get(section, option.encode('utf-8'))

    // 파일의 해시 호출 함수
    def get_hashpath(self, pathname):
        return self.get(path_to_option(pathname), 'hashpath')

    // 언어 보존 여부에 대한 값 검색 함수
    def get_language(self, langid):
       
        if not self.config.has_option('preserve_languages', langid):
            return False
        return self.config.getboolean('preserve_languages', langid)

    // 선택한 모든 언어 목록 반환 함수
    def get_languages(self):
      
        if not self.config.has_section('preserve_languages'):
            return None
        return self.config.options('preserve_languages')

    // 목록 데이터 type 옵션 반환 함수
    def get_list(self, option):
        
        section = "list/%s" % option
        if not self.config.has_section(section):
            return None
        values = []
        for option in sorted(self.config.options(section)):
            values.append(self.config.get(section, option))
        return values

    // get_whitelist_paths 와 get_custom_path 추상화
    def get_paths(self, section):
        
        if not self.config.has_section(section):
            return []
        myoptions = []
        for option in sorted(self.config.options(section)):
            pos = option.find('_')
            if -1 == pos:
                continue
            myoptions.append(option[0:pos])
        values = []
        for option in set(myoptions):
            p_type = self.config.get(section, option + '_type')
            p_path = self.config.get(section, option + '_path')
            values.append((p_type, p_path))
        return values

    // whitelist 경로 반환 함수
    def get_whitelist_paths(self):
         return self.get_paths("whitelist/paths")

     // 사용자 지정 경로 반환 함수
    def get_custom_paths(self):
         return self.get_paths("custom/paths")

    // 트리 보기에 대한 옵션 검색 함수
    def get_tree(self, parent, child):
        option = parent
        if child is not None:
            option += "." + child
        if not self.config.has_option('tree', option):
            return False
        try:
            return self.config.getboolean('tree', option)
        except:
            traceback.print_exc()
            return False

    // Disk에 저장된 옵션 복원 함수    
    def restore(self):
        try:
            self.config.read(bleachbit.options_file)
        except:
            traceback.print_exc()
        if not self.config.has_section("bleachbit"):
            self.config.add_section("bleachbit")
        if not self.config.has_section("hashpath"):
            self.config.add_section("hashpath")
        if not self.config.has_section("list/shred_drives"):
            from bleachbit.FileUtilities import guess_overwrite_paths
            try:
                self.set_list('shred_drives', guess_overwrite_paths())
            except:
                traceback.print_exc()
                logger.error('error setting default shred drives')

        // defaluts 선언
        self.__set_default("auto_hide", True)
        self.__set_default("auto_start", False)
        self.__set_default("check_beta", False)
        self.__set_default("check_online_updates", True)
        self.__set_default("shred", False)
        self.__set_default("exit_done", False)
        self.__set_default("delete_confirmation", True)
        self.__set_default("units_iec", False)

        if 'nt' == os.name:
            self.__set_default("update_winapp2", False)

        if not self.config.has_section('preserve_languages'):
            lang = bleachbit.user_locale
            pos = lang.find('_')
            if -1 != pos:
                lang = lang[0: pos]
            for _lang in set([lang, 'en']):
                logger.info("automatically preserving language '%s'", lang)
                self.set_language(_lang, True)

        // 블리치비트 업그레이드 또는 처음 시작
        if not self.config.has_option('bleachbit', 'version') or \
                self.get('version') != bleachbit.APP_VERSION:
            self.set('first_start', True)

        self.set("version", bleachbit.APP_VERSION)

     // 일반 옵션 설정 함수   
    def set(self, key, value, section='bleachbit', commit=True):
        """Set a general option"""
        self.config.set(section, key.encode('utf-8'), str(value))
        if commit:
            self.__flush()
    
    // 경로의 해시 기억 함수
    def set_hashpath(self, pathname, hashvalue):
        self.set(path_to_option(pathname), hashvalue, 'hashpath')

    // 목록 데이터 타입 값 설정 함수
    def set_list(self, key, values):
        section = "list/%s" % key
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter), value)
            counter += 1
        self.__flush()

   // whitelist 저장 함수
    def set_whitelist_paths(self, values):
        section = "whitelist/paths"
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter) + '_type', value[0])
            self.config.set(section, str(counter) + '_path', value[1])
            counter += 1
        self.__flush()

     // 사용자 지정 목록 저장 함수
    def set_custom_paths(self, values):
        section = "custom/paths"
        if self.config.has_section(section):
            self.config.remove_section(section)
        self.config.add_section(section)
        counter = 0
        for value in values:
            self.config.set(section, str(counter) + '_type', value[0])
            self.config.set(section, str(counter) + '_path', value[1])
            counter += 1
        self.__flush()

    // local값 설정(저장 여부) 함수    
    def set_language(self, langid, value):
        if not self.config.has_section('preserve_languages'):
            self.config.add_section('preserve_languages')
        if self.config.has_option('preserve_languages', langid) and not value:
            self.config.remove_option('preserve_languages', langid)
        else:
            self.config.set('preserve_languages', langid, str(value))
        self.__flush()

     // 트리 보기에 대한 옵션 설정 함수   
    def set_tree(self, parent, child, value):
        """Set an option for the tree view.  The child may be None."""
        if not self.config.has_section("tree"):
            self.config.add_section("tree")
        option = parent
        if child is not None:
            option = option + "." + child
        if self.config.has_option('tree', option) and not value:
            self.config.remove_option('tree', option)
        else:
            self.config.set('tree', option, str(value))
        self.__flush()

    def toggle(self, key):
        """Toggle a boolean key"""
        self.set(key, not self.get(key))


options = Options()
