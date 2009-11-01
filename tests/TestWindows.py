# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Test case for module Windows
"""



import sys
import unittest

if 'win32' == sys.platform:
    import _winreg

sys.path.append('.')
from bleachbit.Windows import *



class WindowsTestCase(unittest.TestCase):
    """Test case for module Windows"""


    def test_delete_locked_file(self):
        """Unit test for delete_locked_file"""
        fn = "c:\\bleachbit_deleteme_later"
        f = open(fn, "w")
        f.close()
        delete_locked_file(fn)


    def test_delete_registry_key(self):
        """Unit test for delete_registry_key"""
        # (return value, key, really_delete)
        tests = ( (False, 'HKCU\\Software\\BleachBit\\DoesNotExist', False, ) ,
            (False, 'HKCU\\Software\\BleachBit\\DoesNotExist', True, ) ,
            (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', False, ) ,
            (True, 'HKCU\\Software\\BleachBit\\DeleteThisKey', True, ) , )


        # create a nested key
        key = 'Software\\BleachBit\\DeleteThisKey'
        subkey = key + '\\AndThisKey'
        hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, subkey )
        hkey.Close()

        # test
        for test in tests:
            return_value = delete_registry_key(test[1], test[2])
            self.assertEqual(test[0], return_value)


    def test_delete_registry_value(self):
        """Unit test for delete_registry_value"""

        ##
        ## test: value does exist
        ##

        # create a name-value pair
        key = 'Software\\BleachBit'
        hkey = _winreg.CreateKey( _winreg.HKEY_CURRENT_USER, key )

        value_name = 'delete_this_value_name'
        _winreg.SetValueEx( hkey, value_name , 0, _winreg.REG_SZ, 'delete this value')
        hkey.Close()

        # delete and confirm
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, False), True)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, True), True)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, False), False)
        self.assertEqual(delete_registry_value('HKCU\\' + key, value_name, True), False)


        ##
        ## test: value does not exist
        ##
        self.assertEqual(delete_registry_value('HKCU\\' + key, 'doesnotexist', False), False)
        self.assertEqual(delete_registry_value('HKCU\\' + key, 'doesnotexist', True), False)
        self.assertEqual(delete_registry_value('HKCU\\doesnotexist', value_name, False), False)
        self.assertEqual(delete_registry_value('HKCU\\doesnotexist', value_name, True), False)


    def test_enumerate_processes(self):
        processes = enumerate_processes()
        for process in processes:
            self.assertEqual(process, process.lower())
            self.assert_(len(process) > 0)
        self.assert_('explorer.exe' in processes)


    def test_get_fixed_drives(self):
        """Unit test for get_fixed_drives"""
        drives = []
        for drive in get_fixed_drives():
            drives.append(drive)
            self.assertEqual(drive, drive.upper())
        self.assert_("C:\\" in drives)


    def test_empty_recycle_bin(self):
        """Unit test for empty_recycle_bin"""
        for drive in get_fixed_drives():
            ret = empty_recycle_bin(drive, really_delete = False)
            self.assert_ (isinstance(ret, (int, long)))


    def test_split_registry_key(self):
        """Unit test for split_registry_key"""
        tests = ( ('HKCU\\Software', _winreg.HKEY_CURRENT_USER, 'Software'),
            ('HKLM\\SOFTWARE', _winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE') )
        for (input_key, expected_hive, expected_key) in tests:
            (hive, key) = split_registry_key(input_key)
            self.assertEqual(expected_hive, hive)
            self.assertEqual(expected_key, key)


    def test_start_with_computer(self):
            """Unit test for start_with_computer*"""
            b = start_with_computer_check()
            self.assert_(isinstance(b, bool))
            # opposite setting
            start_with_computer(not b)
            two_b = start_with_computer_check()
            self.assert_(isinstance(two_b, bool))
            self.assertEqual(b, not two_b)
            # original setting
            start_with_computer(b)
            three_b = start_with_computer_check()
            self.assert_(isinstance(b, bool))
            self.assertEqual(b, three_b)



def suite():
    return unittest.makeSuite(WindowsTestCase)


if __name__ == '__main__' and sys.platform == 'win32':
    unittest.main()
