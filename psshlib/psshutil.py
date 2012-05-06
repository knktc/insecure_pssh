# Copyright (c) 2009-2012, Andrew McNabb
# Copyright (c) 2003-2008, Brent N. Chun
# Modified 2012 by knktc

import fcntl
import string
import sys

HOST_FORMAT = 'Host format is [user:[password]@]host[:port] [user]'


def read_host_files(paths, default_user=None, default_port=None, default_password=None):
    """Reads the given host files.

    Returns a list of (host, port, user) quadruples.
    """
    hosts = []
    if paths:
        for path in paths:
            hosts.extend(read_host_file(path, default_user=default_user))
    return hosts


def read_host_file(path, default_user=None, default_port=None, default_password=None):
    """Reads the given host file.

    Lines are of the form: host[:port] [user name] [password].
    Returns a list of (host, port, user, password) quadruples.
    """
    lines = []
    f = open(path)
    for line in f:
        lines.append(line.strip())
    f.close()

    hosts = []
    for line in lines:
        # Skip blank lines or lines starting with #
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        host, port, user, password = parse_host_entry(line, default_user, default_port, default_password)
        if host:
            hosts.append((host, port, user, password))
    return hosts


# TODO: deprecate the second host field and standardize on the
# [user@]host[:port] format.
def parse_host_entry(line, default_user, default_port, default_password):
    """Parses a single host entry.

    This may take either the of the form [user:[password]@]host[:port] or
    host[:port][ user][ password].

    Returns a (host, port, user, password) quadruple.
    """
    fields = line.split()
    if len(fields) > 3:
        sys.stderr.write('Bad line: "%s". Format should be'
                ' [user[:password]@]host[:port][ user][ password]\n' % line)
        return None, None, None, None
    host_field = fields[0]
    host, port, user, password = parse_host(host_field, default_port=default_port)
    if len(fields) == 3:
        if user is None:
            user = fields[1]
        else:
            sys.stderr.write('User specified twice in line: "%s"\n' % line)
            return None, None, None, None
        if password is None:
            password = fields[2]
        else:
            sys.stderr.write('Password specified twice in line: "%s"\n' % line)
            return None, None, None, None        
    if user is None:
        user = default_user
    if password is None:
        password = default_password
    return host, port, user, password


def parse_host_string(host_string, default_user=None, default_port=None, default_password=None):
    """Parses a whitespace-delimited string of "[user[:password]@]host[:port]" entries.

    Returns a list of (host, port, user, password) quadruples.
    """
    hosts = []
    entries = host_string.split()
    for entry in entries:
        hosts.append(parse_host(entry, default_user, default_port, default_password))
    return hosts


def parse_host(host, default_user=None, default_port=None, default_password=None):
    """Parses host entries of the form "[user[:password]@]host[:port]".

    Returns a (host, port, user, password) quadruple.
    """
    # TODO: when we stop supporting Python 2.4, switch to using str.partition.
    user = default_user
    port = default_port
    password = default_password
    if '@' in host:
        login, host = host.rsplit('@', 1)
        if ':' in login:
            user, password = login.split(':', 1)
        else:
            user = login
    
    if ':' in host:
        host, port = host.rsplit(':', 1)
    return (host, port, user, password)


def set_cloexec(filelike):
    """Sets the underlying filedescriptor to automatically close on exec.

    If set_cloexec is called for all open files, then subprocess.Popen does
    not require the close_fds option.
    """
    fcntl.fcntl(filelike.fileno(), fcntl.FD_CLOEXEC, 1)
