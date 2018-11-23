# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-


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
Preferences dialog
"""

//클래스
from __future__ import absolute_import, print_function

from bleachbit import _, _p, online_update_notification_enabled
from bleachbit.Options import options
from bleachbit import GuiBasic


//import 선언
import gtk
import logging
import os
import sys
import traceback

if 'nt' == os.name:
    from bleachbit import Windows
if 'posix' == os.name:
    from bleachbit import Unix

logger = logging.getLogger(__name__)

LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2

// 기본 설정 대화 상자 표시 및 변경 사항 저장하는 클래스
class PreferencesDialog:

    
    // 초기화 함수
    // dialog창을 띄우기 위해 초기화함. self, parent, cb_refresh_operations를 매개변수로 사용
    def __init__(self, parent, cb_refresh_operations):
        self.cb_refresh_operations = cb_refresh_operations

        self.parent = parent
        self.dialog = gtk.Dialog(title=_("Preferences"),
                                 parent=parent,
                                 flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        self.dialog.set_default_size(300, 200)

        //notebook 변수 선언
        notebook = gtk.Notebook()
        notebook.append_page(self.__general_page(), gtk.Label(_("General")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_CUSTOM), gtk.Label(_("Custom")))
        notebook.append_page(self.__drives_page(), gtk.Label(_("Drives")))
        
        // 만약 'posix'가 os.name 이면 Unix 파일 import하여 notebook에 append_page실행
        if 'posix' == os.name:
            notebook.append_page(
                self.__languages_page(), gtk.Label(_("Languages")))
        notebook.append_page(self.__locations_page(
            LOCATIONS_WHITELIST), gtk.Label(_("Whitelist")))

        //self.diaglof 실행
        self.dialog.vbox.pack_start(notebook, True)
        //self.dialog에 버튼 더함
        self.dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

    // 콜백 함수를 사용하여 옵션 전환     
    def __toggle_callback(self, cell, path):
        
        options.toggle(path)
        // online_update_notification_enabled 이면 
        if online_update_notification_enabled:
            self.cb_beta.set_sensitive(options.get('check_online_updates'))
            // 'nt' == os.name이면 Windows파일 import하여 self.cb_winapp2.set_sensitive 실행
            if 'nt' == os.name:
                self.cb_winapp2.set_sensitive(
                    options.get('check_online_updates'))
        // 만약 'auto_hide' == path이면 self.cb_refresh_operations() 수행         
        if 'auto_hide' == path:
            self.cb_refresh_operations()
        // 만약  'auto_start' == path이고   
        if 'auto_start' == path:
            // 'nt' == os.name이면 Windows파일 import하여  swc = Windows.start_with_computer 선언
            if 'nt' == os.name:
                swc = Windows.start_with_computer
            // 'posix' == os.name이면 Unix파일 import하여 swc = Unix.start_with_computer선언
            if 'posix' == os.name:
                swc = Unix.start_with_computer
            try:
                swc(options.get(path))
            except:
                traceback.print_exc()
                dlg = gtk.MessageDialog(self.parent,
                                        type=gtk.MESSAGE_ERROR,
                                        buttons=gtk.BUTTONS_OK,
                                        message_format=str(sys.exc_info()[1]))
                dlg.run()
                dlg.destroy()

    // 일반 페이지가 포함된 위젯 반환
    def __general_page(self):
      
        //'nt' == os.name이면 Windows파일 import하여  swc = Windows.start_with_computer_check 선언
        if 'nt' == os.name:
            swcc = Windows.start_with_computer_check
        // 'posix' == os.name이면 Unix파일 import하여 swc = Unix.start_with_computer_check 선언
        if 'posix' == os.name:
            swcc = Unix.start_with_computer_check

        options.set('auto_start', swcc())

        vbox = gtk.VBox()
        
        // online_update_notification_enabled 이면
        if online_update_notification_enabled:
            cb_updates = gtk.CheckButton(
                _("Check periodically for software updates via the Internet"))
            cb_updates.set_active(options.get('check_online_updates'))
            cb_updates.connect(
                'toggled', self.__toggle_callback, 'check_online_updates')
            cb_updates.set_tooltip_text(
                _("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update."))
            vbox.pack_start(cb_updates, False)

            updates_box = gtk.VBox()
            updates_box.set_border_width(10)

            self.cb_beta = gtk.CheckButton(_("Check for new beta releases"))
            self.cb_beta.set_active(options.get('check_beta'))
            self.cb_beta.set_sensitive(options.get('check_online_updates'))
            self.cb_beta.connect(
                'toggled', self.__toggle_callback, 'check_beta')
            updates_box.pack_start(self.cb_beta, False)

            if 'nt' == os.name:
                self.cb_winapp2 = gtk.CheckButton(
                    _("Download and update cleaners from community (winapp2.ini)"))
                self.cb_winapp2.set_active(options.get('update_winapp2'))
                self.cb_winapp2.set_sensitive(
                    options.get('check_online_updates'))
                self.cb_winapp2.connect(
                    'toggled', self.__toggle_callback, 'update_winapp2')
                updates_box.pack_start(self.cb_winapp2, False)

            vbox.pack_start(updates_box, False)

        // '무관한 클리너 숨김' 버튼 생성 및 연결
        cb_auto_hide = gtk.CheckButton(_("Hide irrelevant cleaners"))
        cb_auto_hide.set_active(options.get('auto_hide'))
        cb_auto_hide.connect('toggled', self.__toggle_callback, 'auto_hide')
        vbox.pack_start(cb_auto_hide, False)

        // '파일 삭제 기능' 버튼 생성 및 연결
        cb_shred = gtk.CheckButton(_("Overwrite contents of files to prevent recovery"))
        cb_shred.set_active(options.get('shred'))
        cb_shred.connect('toggled', self.__toggle_callback, 'shred')
        cb_shred.set_tooltip_text(
            _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower."))
        vbox.pack_start(cb_shred, False)

        // '블리치비트 시작' 버튼 생성 및 연결
        cb_start = gtk.CheckButton(_("Start BleachBit with computer"))
        cb_start.set_active(options.get('auto_start'))
        cb_start.connect('toggled', self.__toggle_callback, 'auto_start')
        vbox.pack_start(cb_start, False)

       
        // 클리너 완료 후 프로그램 종료 버튼 생성 및 연결
        cb_exit = gtk.CheckButton(_("Exit after cleaning"))
        cb_exit.set_active(options.get('exit_done'))
        cb_exit.connect('toggled', self.__toggle_callback, 'exit_done')
        vbox.pack_start(cb_exit, False)

        // 삭제 전 확인 버튼 생성 및 연결
        cb_popup = gtk.CheckButton(_("Confirm before delete"))
        cb_popup.set_active(options.get('delete_confirmation'))
        cb_popup.connect(
            'toggled', self.__toggle_callback, 'delete_confirmation')
        vbox.pack_start(cb_popup, False)

        
        cb_units_iec = gtk.CheckButton(
            _("Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)"))
        cb_units_iec.set_active(options.get("units_iec"))
        cb_units_iec.connect('toggled', self.__toggle_callback, 'units_iec')
        vbox.pack_start(cb_units_iec, False)
        return vbox
    
    // 드라이브 페이지가 포함된 위젯 반환 함수
    def __drives_page(self):
        
        // 드라이브 추가를 위한 콜백함수
        def add_drive_cb(button):
            // title과 pathname 선언
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=gtk.STOCK_ADD)
            if pathname:
                liststore.append([pathname])
                pathnames.append(pathname)
                options.set_list('shred_drives', pathnames)
        
        // 드라이버 제거를 위한 콜백 함수
        def remove_drive_cb(button):
           
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                // 아무것도 선택되지 않으면
                return
            pathname = model[_iter][0]
            liststore.remove(_iter)
            pathnames.remove(pathname)
            options.set_list('shred_drives', pathnames)

        vbox = gtk.VBox()

       
        notice = gtk.Label(
            _("Choose a writable folder for each drive for which to overwrite free space."))
        notice.set_line_wrap(True)
        vbox.pack_start(notice, False)

        liststore = gtk.ListStore(str)

        pathnames = options.get_list('shred_drives')
        if pathnames:
            pathnames = sorted(pathnames)
        if not pathnames:
            pathnames = []
        for pathname in pathnames:
            liststore.append([pathname])
        treeview = gtk.TreeView(model=liststore)
        crt = gtk.CellRendererText()
        tvc = gtk.TreeViewColumn(None, crt, text=0)
        treeview.append_column(tvc)

        vbox.pack_start(treeview)

       
        // 추가버튼 추가
        button_add = gtk.Button(_p('button', 'Add'))
        button_add.connect("clicked", add_drive_cb)
       
        //제거버튼 추가
        button_remove = gtk.Button(_p('button', 'Remove'))
        button_remove.connect("clicked", remove_drive_cb)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        button_box.pack_start(button_add)
        button_box.pack_start(button_remove)
        vbox.pack_start(button_box, False)

        return vbox

    // 언어 페이지가 포함된 위젯 반환 함수
    def __languages_page(self):
        
        // 보존 row를 전환하기 위한 콜백 함수
        def preserve_toggled_cb(cell, path, liststore):
            __iter = liststore.get_iter_from_string(path)
            value = not liststore.get_value(__iter, 0)
            liststore.set(__iter, 0, value)
            langid = liststore[path][1]
            options.set_language(langid, value)

        vbox = gtk.VBox()

        notice = gtk.Label(
            _("All languages will be deleted except those checked."))
        vbox.pack_start(notice, False)

        // 데이터 채움
        liststore = gtk.ListStore('gboolean', str, str)
        for lang, native in sorted(Unix.Locales.native_locale_names.items()):
            liststore.append([(options.get_language(lang)), lang, native])

       // 트리뷰 생성
        treeview = gtk.TreeView(liststore)

        //컬럼뷰 생성
        self.renderer0 = gtk.CellRendererToggle()
        self.renderer0.set_property('activatable', True)
        self.renderer0.connect('toggled', preserve_toggled_cb, liststore)
        self.column0 = gtk.TreeViewColumn(
            _("Preserve"), self.renderer0, active=0)
        treeview.append_column(self.column0)

        self.renderer1 = gtk.CellRendererText()
        self.column1 = gtk.TreeViewColumn(_("Code"), self.renderer1, text=1)
        treeview.append_column(self.column1)

        self.renderer2 = gtk.CellRendererText()
        self.column2 = gtk.TreeViewColumn(_("Name"), self.renderer2, text=2)
        treeview.append_column(self.column2)
        treeview.set_search_column(2)

        // 종료
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow)
        return vbox

    // 파일 및 폴더 목록이 포함된 위젯 되돌리기 함수
    def __locations_page(self, page_type):
       
        // 파일 추가를 위한 콜백 함수
        def add_whitelist_file_cb(button):
            
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning("'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_whitelist_paths(pathnames)

        // 파일 추가를 위한 콜백 함수        
        def add_whitelist_folder_cb(button):
            
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning("'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_whitelist_paths(pathnames)

        // 경로를 삭제하기 위한 콜백 함수        
        def remove_whitelist_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                // 아무것도 선택되지 않았다면
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_whitelist_paths(pathnames)

        // 파일 추가를 위한 콜백 함수            
        def add_custom_file_cb(button):
            
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning("'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_custom_paths(pathnames)

        // 폴더 추가를 위한 콜백 함수         
        def add_custom_folder_cb(button):
            
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning("'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_custom_paths(pathnames)

         // 경로 삭제를 위한 콜백 함수       
        def remove_custom_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                // 아무것도 선택되지 
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_custom_paths(pathnames)

        vbox = gtk.VBox()

        // 데이터 가져옴
        if LOCATIONS_WHITELIST == page_type:
            pathnames = options.get_whitelist_paths()
        elif LOCATIONS_CUSTOM == page_type:
            pathnames = options.get_custom_paths()
        liststore = gtk.ListStore(str, str)
        for paths in pathnames:
            type_code = paths[0]
            type_str = None
            if type_code == 'file':
                type_str = _('File')
            elif type_code == 'folder':
                type_str = _('Folder')
            else:
                raise RuntimeError("Invalid type code: '%s'" % type_code)
            path = paths[1]
            liststore.append([type_str, path])

        if LOCATIONS_WHITELIST == page_type:
           
            notice = gtk.Label(
                _("Theses paths will not be deleted or modified."))
        elif LOCATIONS_CUSTOM == page_type:
            notice = gtk.Label(
                _("These locations can be selected for deletion."))
        vbox.pack_start(notice, False)

        // 트리 뷰 생성
        treeview = gtk.TreeView(liststore)

        // 칼럼 뷰 생성
        self.renderer0 = gtk.CellRendererText()
        self.column0 = gtk.TreeViewColumn(_("Type"), self.renderer0, text=0)
        treeview.append_column(self.column0)

        self.renderer1 = gtk.CellRendererText()
       
        self.column1 = gtk.TreeViewColumn(_("Path"), self.renderer1, text=1)
        treeview.append_column(self.column1)
        treeview.set_search_column(1)

        // 트리 뷰 끝냄
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.pack_start(swindow)

       // 리스트 수정 버튼 생성 
        button_add_file = gtk.Button(_p('button', 'Add file'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_file.connect("clicked", add_whitelist_file_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_file.connect("clicked", add_custom_file_cb)

        button_add_folder = gtk.Button(_p('button', 'Add folder'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_folder.connect("clicked", add_whitelist_folder_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_folder.connect("clicked", add_custom_folder_cb)

        button_remove = gtk.Button(_p('button', 'Remove'))
        if LOCATIONS_WHITELIST == page_type:
            button_remove.connect("clicked", remove_whitelist_path_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_remove.connect("clicked", remove_custom_path_cb)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        button_box.pack_start(button_add_file)
        button_box.pack_start(button_add_folder)
        button_box.pack_start(button_remove)
        vbox.pack_start(button_box, False)

        // 페이지 반환
        return vbox

    // dialog 
    def run(self):
        """Run the dialog"""
        self.dialog.show_all()
        self.dialog.run()
        self.dialog.destroy()
