from pwn import *
import inspect
import os
import subprocess


def libc_search(query, select=0):
    '''query should be a dict like {'printf':0x6b0, ......}'''
    HOME = os.path.expanduser('~')
    RECORD = '{}/.libcdb_path'.format(HOME)
    if not os.access(RECORD, os.F_OK):
        LIBCDB_PATH = raw_input('Please input the absolute libcdb path:')
        f = open(RECORD, 'w')
        f.write(LIBCDB_PATH)
        f.close()
    else:
        LIBCDB_PATH = open(RECORD).read()
 
    LIBCDB_PATH = LIBCDB_PATH.strip()
    cwd = os.getcwd()
    os.chdir(LIBCDB_PATH)
    args = ''
    for name in query:
        args += '{} {} '.format(name, hex(query[name])[2:])
    p = os.popen('./find {}'.format(args))
    result = p.readlines()
    if len(result)==0:
        log.failure('Unable to find libc with libc-database')
        os.chdir(cwd)
        return None
    else:
        if (select==0 and len(result)>1) or select>=len(result):
            select = ui.options('choose a possible libc', result)
        
        libc_path = './db/{}.so'.format(result[select].split()[2][:-1])
        e = ELF(libc_path)
        os.chdir(cwd)
        return e
        
    
def one_gadgets(binary, offset=0, use_cache=True):
    HOME = os.path.expanduser('~')
    ONE_DIR = '{}/.one_gadgets'.format(HOME)
    if isinstance(binary, ELF):
        binary = binary.path
    if not os.access(ONE_DIR, os.F_OK):os.mkdir(ONE_DIR)
     
    if not os.access(binary, os.R_OK):
        log.failure("Invalid path {} to binary".format(binary))
        return []
    
    sha1 = sha1filehex(binary)
    cache = "{}/{}".format(ONE_DIR, sha1)
    
    if os.access(cache, os.R_OK) and use_cache:
        log.success("using cached gadgets {}".format(cache))
        with open(cache, 'r') as f:
            gadgets = [int(_) for _ in f.read().split()]
            if offset:
                log.info("add offset {} to gadgets".format(offset))
                gadgets = [_+offset for _ in gadgets]
            return gadgets

    else:
        p = subprocess.Popen(["one_gadget", "-r",  binary], stdout=PIPE, stderr=PIPE)
        ret_code = p.wait()
        st_o, st_e = p.communicate()
        if ret_code == 0:
            if use_cache:
                with open(cache, 'w') as f:
                    f.write(st_o)
            gadgets = [int(_) for _ in st_o.split()]
            log.success("dump one_gadgets from {} : {}".format(binary, gadgets))
            if offset:
                log.info("add offset {} to gadgets".format(offset))
                gadgets = [_+offset for _ in gadgets]
            return gadgets
        else:
            log.failure("dump one_gadgets from {} failed".format(binary))
            log.info("error msg:\n"+st_e)
            return []
            
def instruction_log(arg=0):
    def _log_wrapper(func):
        def wrapper(*args, **kargs):
            stack = inspect.stack()
            log.info('{}:{}'.format(stack[1][2], stack[1][4][0]))
            ret_val = func(*args, **kargs)
            return ret_val
        return wrapper
    return _log_wrapper