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
Wipe memory
"""

// 클래스
from __future__ import absolute_import, print_function

from bleachbit import FileUtilities
from bleachbit import General

//import 선언
import logging
import os
import re
import subprocess
import sys
import traceback

logger = logging.getLogger(__name__)

// 사용 중인 스왑 디바이스 수 계산함수
def count_swap_linux():
    
    f = open("/proc/swaps")
    count = 0
    for line in f:
        if line[0] == '/':
            count += 1
    return count

// swapon-s 의 출력 반환
def get_proc_swaps():
    
    (rc, stdout, _) = General.run_external(['swapon', '-s'])
    if 0 == rc:
        return stdout
    logger.debug('"swapoff -s" failed so falling back to /proc/swaps')
    return open("/proc/swaps").read()

// 스왑오프 출력을 구문 분석하고 디바이스 이름을 반환
def parse_swapoff(swapoff):
    
    ret = re.search('^swapoff (\w* )?(/[\w/.-]+)$', swapoff)
    if not ret:
        # no matches
        return None
    return ret.group(2)

// 디바이스의 Linux 스왑 및 목록 사용 안 함
def disable_swap_linux():
   
    if 0 == count_swap_linux():
        return
    logger.debug('disabling swap"')
    args = ["swapoff", "-a", "-v"]
    (rc, stdout, stderr) = General.run_external(args)
    if 0 != rc:
        raise RuntimeError(stderr.replace("\n", ""))
    devices = []
    for line in stdout.split('\n'):
        line = line.replace('\n', '')
        if '' == line:
            continue
        ret = parse_swapoff(line)
        if ret is None:
            raise RuntimeError("Unexpected output:\nargs='%(args)s'\nstdout='%(stdout)s'\nstderr='%(stderr)s'"
                               % {'args': str(args), 'stdout': stdout, 'stderr': stderr})
        devices.append(ret)
    return devices

// 리눅스 스왑 
def enable_swap_linux():
    
    logger.debug('re-enabling swap"')
    args = ["swapon", "-a"]
    p = subprocess.Popen(args, stderr=subprocess.PIPE)
    p.wait()
    outputs = p.communicate()
    if 0 != p.returncode:
        raise RuntimeError(outputs[1].replace("\n", ""))

// 현재 프로세스를 Linux Out-of-memory의 주요 대상으로 설정 함수
def make_self_oom_target_linux():
    
    path = '/proc/%d/oom_score_adj' % os.getpid()
    if os.path.exists(path):
        open(path, 'w').write('1000')
    else:
        path = '/proc/%d/oomadj' % os.getpid()
        if os.path.exists(path):
            open(path, 'w').write('15')
    # OOM likes nice processes
    logger.debug('new nice value %d', os.nice(19))
    # OOM prefers non-privileged processes
    try:
        uid = General.getrealuid()
        if uid > 0:
            logger.debug('dropping privileges of pid %d to uid %d', os.getpid(), uid)
            os.seteuid(uid)
    except:
        traceback.print_exc()

// 할당되지 않은 메모리 채우는 함수
def fill_memory_linux():
   
    report_free()
    allocbytes = int(physical_free() * 0.4)
    if allocbytes < 1024:
        return
    bytes_str = FileUtilities.bytes_to_human(allocbytes)
    logger.info('allocating and wiping %s (%d B) of memory', bytes_str, allocbytes)
    try:
        buf = '\x00' * allocbytes
    except MemoryError:
        pass
    else:
        fill_memory_linux()
        logger.debug('freeing %s of memory" % bytes_str')
        del buf
    report_free()

// 할당되지 않은 메모리 채우는 함수
def get_swap_size_linux(device, proc_swaps=None):
    
    if proc_swaps is None:
        proc_swaps = get_proc_swaps()
    line = proc_swaps.split('\n')[0]
    if not re.search('Filename\s+Type\s+Size', line):
        raise RuntimeError("Unexpected first line in swap summary '%s'" % line)
    for line in proc_swaps.split('\n')[1:]:
        ret = re.search("%s\s+\w+\s+([0-9]+)\s" % device, line)
        if ret:
            return int(ret.group(1)) * 1024
    raise RuntimeError("error: cannot find size of swap device '%s'\n%s" %
                       (device, proc_swaps))

// 스왑 디바이스의 uuid 찾는 함수
def get_swap_uuid(device):
    
    uuid = None
    args = ['blkid', device, '-s', 'UUID']
    (_, stdout, _) = General.run_external(args)
    for line in stdout.split('\n'):
        # example: /dev/sda5: UUID="ee0e85f6-6e5c-42b9-902f-776531938bbf"
        ret = re.search("^%s: UUID=\"([a-z0-9-]+)\"" % device, line)
        if ret is not None:
            uuid = ret.group(1)
    logger.debug("uuid(%s)='%s'", device, uuid)
    return uuid


def physical_free_darwin(run_vmstat=None):
    def parse_line(k, v):
        return k, int(v.strip(" ."))

    // 가상 메모리 통계 함수
    def get_page_size(line):
        m = re.match(
            r"Mach Virtual Memory Statistics: \(page size of (\d+) bytes\)",
            line)
        if m is None:
            raise RuntimeError("Can't parse vm_stat output")
        return int(m.groups()[0])
    if run_vmstat is None:
        def run_vmstat():
            return subprocess.check_output(["vm_stat"])
    output = iter(run_vmstat().split("\n"))
    page_size = get_page_size(next(output))
    vm_stat = dict(parse_line(*l.split(":")) for l in output if l != "")
    return vm_stat["Pages free"] * page_size

// 리눅스에서 실제 사용 가능한 메모리 반환
def physical_free_linux():
    
    f = open("/proc/meminfo")
    free_bytes = 0
    for line in f:
        line = line.replace("\n", "")
        ret = re.search('(MemFree|Cached):[ ]*([0-9]*) kB', line)
        if ret is not None:
            kb = int(ret.group(2))
            free_bytes += kb * 1024
    if free_bytes > 0:
        return free_bytes
    else:
        raise Exception("unknown")

// Windows애서 실제 사용 가능한 메모리 반환하는 함수
def physical_free_windows():
   

    from ctypes import c_long, c_ulonglong
    from ctypes.wintypes import Structure, sizeof, windll, byref

    class MEMORYSTATUSEX(Structure):
        _fields_ = [
            ('dwLength', c_long),
            ('dwMemoryLoad', c_long),
            ('ullTotalPhys', c_ulonglong),
            ('ullAvailPhys', c_ulonglong),
            ('ullTotalPageFile', c_ulonglong),
            ('ullAvailPageFile', c_ulonglong),
            ('ullTotalVirtual', c_ulonglong),
            ('ullAvailVirtual', c_ulonglong),
            ('ullExtendedVirtual', c_ulonglong),
        ]

    def GlobalMemoryStatusEx():
        x = MEMORYSTATUSEX()
        x.dwLength = sizeof(x)
        windll.kernel32.GlobalMemoryStatusEx(byref(x))
        return x

    z = GlobalMemoryStatusEx()
    print(z)
    return z.ullAvailPhys

// 메모리 반환 함수
def physical_free():
    if sys.platform.startswith('linux'):
        return physical_free_linux()
    elif 'win32' == sys.platform:
        return physical_free_windows()
    elif 'darwin' == sys.platform:
        return physical_free_darwin()
    else:
        raise RuntimeError('unsupported platform for physical_free()')

// 리눅스 스왑 파일을 복사한 다음 다시 초기화 하는 함수
def report_free():
   
    bytes_free = physical_free()
    bytes_str = FileUtilities.bytes_to_human(bytes_free)
    logger.debug('physical free: %s (%d B)', bytes_str, bytes_free)


def wipe_swap_linux(devices, proc_swaps):
    """Shred the Linux swap file and then reinitilize it"""
    if devices is None:
        return
    if 0 < count_swap_linux():
        raise RuntimeError('Cannot wipe swap while it is in use')
    for device in devices:
        logger.info("wiping swap device '%s'", device)
        safety_limit_bytes = 29 * 1024 ** 3  # 29 gibibytes
        actual_size_bytes = get_swap_size_linux(device, proc_swaps)
        if actual_size_bytes > safety_limit_bytes:
            raise RuntimeError(
                'swap device %s is larger (%d) than expected (%d)' %
                (device, actual_size_bytes, safety_limit_bytes))
        uuid = get_swap_uuid(device)
        // wipe 실행
        FileUtilities.wipe_contents(device, truncate=False)
        // 초기화
        logger.debug('reinitializing swap device %s', device)
        args = ['mkswap', device]
        if uuid:
            args.append("-U")
            args.append(uuid)
        (rc, _, stderr) = General.run_external(args)
        if 0 != rc:
            raise RuntimeError(stderr.replace("\n", ""))

// 할당되지 않은 메모리 지우는 함수
def wipe_memory():
    
    // 파일 캐시
    proc_swaps = get_proc_swaps()
    devices = disable_swap_linux()
    yield True  
    logger.debug('detected swap devices: ' + str(devices))
    wipe_swap_linux(devices, proc_swaps)
    yield True
    child_pid = os.fork()
    if 0 == child_pid:
        make_self_oom_target_linux()
        fill_memory_linux()
        sys.exit(0)
    else:
        logger.debug('wipe_memory() pid %d waiting for child pid %d', os.getpid(), child_pid)
        rc = os.waitpid(child_pid, 0)[1]
        if 0 != rc:
            logger.warning('child process returned code %d', rc)
    enable_swap_linux()
    yield 0 
