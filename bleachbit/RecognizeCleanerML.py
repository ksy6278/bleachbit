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
Check local CleanerML files as a security measure
"""
// 클래스 선언
from __future__ import absolute_import, print_function
from bleachbit import _, _p
from bleachbit.CleanerML import list_cleanerml_files
from bleachbit.Options import options

// import문 
import bleachbit
import hashlib
import logging
import os
import sys


logger = logging.getLogger(__name__)

KNOWN = 1
CHANGED = 2
NEW = 3

// 클리너 정의 변경에 대한 dialog 보여주는 함수
def cleaner_change_dialog(changes, parent):

    // 체크 박스 클릭에 대한 콜백 함수
    def toggled(cell, path, model):
       
        __iter = model.get_iter_from_string(path)
        value = not model.get_value(__iter, 0)
        model.set(__iter, 0, value)

    import pygtk
    pygtk.require('2.0')
    import gtk

    dialog = gtk.Dialog(title=_("Security warning"),
                        parent=parent,
                        flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
    dialog.set_default_size(600, 500)

    // 경고 생성
    warnbox = gtk.HBox()
    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
    warnbox.pack_start(image, False)
   
    label = gtk.Label(
        _("These cleaner definitions are new or have changed. Malicious definitions can damage your system. If you do not trust these changes, delete the files or quit."))
    label.set_line_wrap(True)
    warnbox.pack_start(label, True)
    dialog.vbox.pack_start(warnbox, False)

   // 트리뷰 생성
    import gobject
    liststore = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING)
    treeview = gtk.TreeView(model=liststore)

    renderer0 = gtk.CellRendererToggle()
    renderer0.set_property('activatable', True)
    renderer0.connect('toggled', toggled, liststore)
    
    treeview.append_column(
        gtk.TreeViewColumn(_p('column_label', 'Delete'), renderer0, active=0))
    renderer1 = gtk.CellRendererText()
    
    treeview.append_column(
        gtk.TreeViewColumn(_p('column_label', 'Filename'), renderer1, text=1))

    // 트리 뷰 채우기
    for change in changes:
        liststore.append([False, change[0]])

    // dialog 채우기
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.add_with_viewport(treeview)
    dialog.vbox.pack_start(scrolled_window)

    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
    dialog.add_button(gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE)

    // dialog 실행
    dialog.show_all()
    while True:
        if gtk.RESPONSE_ACCEPT != dialog.run():
            sys.exit(0)
        delete = []
        for row in liststore:
            b = row[0]
            path = row[1]
            if b:
                delete.append(path)
        if 0 == len(delete):
            # no files selected to delete
            break
        import GuiBasic
        if not GuiBasic.delete_confirmation_dialog(parent, mention_preview=False):
            
            continue
        for path in delete:
            logger.info("deleting unrecognized CleanerML '%s'", path)
            os.remove(path)
        break
    dialog.destroy()

// 문자열에 대한 해시의 16진수 digest 반환
def hashdigest(string):
   

    
    return hashlib.sha512(string).hexdigest()

// 보안적 조치로 local CleanerML 파일 체크하는 클래스
class RecognizeCleanerML:

    // 초기화 함수
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        try:
            self.salt = options.get('hashsalt')
        except bleachbit.NoOptionError:
            self.salt = hashdigest(os.urandom(512))
            options.set('hashsalt', self.salt)
        self.__scan()

     // 경로이름 인식 함수   
    def __recognized(self, pathname):
        with open(pathname) as f:
            body = f.read()
        new_hash = hashdigest(self.salt + body)
        try:
            known_hash = options.get_hashpath(pathname)
        except bleachbit.NoOptionError:
            return NEW, new_hash
        if new_hash == known_hash:
            return KNOWN, new_hash
        return CHANGED, new_hash

    // 파일 찾는 
    def __scan(self):
        changes = []
        for pathname in sorted(list_cleanerml_files(local_only=True)):
            pathname = os.path.abspath(pathname)
            (status, myhash) = self.__recognized(pathname)
            if NEW == status or CHANGED == status:
                changes.append([pathname, status, myhash])
        if len(changes) > 0:
            cleaner_change_dialog(changes, self.parent_window)
            for change in changes:
                pathname = change[0]
                myhash = change[2]
                logger.info("remembering CleanerML file '%s'", pathname)
                if os.path.exists(pathname):
                    options.set_hashpath(pathname, myhash)
