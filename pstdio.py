import gdb
import os
import sys


class Pstdio(object):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.commands = [c for c in dir(self) if callable(getattr(self, c)) and not c.startswith("_")]

    def data(self, *arg):
        '''
        Set stdio of the program to the tmp file which store the DATA.
        Usage:
            pstdio data [/x] [DATA]
            OPTIONS:
                 /x : Enable interpretation of hex 
        '''

        if len(arg) == 0:
            self.help("data")
            return
        tmp_file = "/tmp/pstdio_3Dae12"
        if len(arg) == 2 and arg[0] == '/x':
            enable_hex = True
            data = arg[1]
        else:
            enable_hex = False
            data = arg[0]
        if enable_hex:
            hexed_data = ''
            i = 0
            while i < len(data):
                if i+3 < len(data) and data[i] == '\\' and data[i+1].upper() == 'X':
                    try:
                        hexed_data += chr(int(data[i+2]+data[i+3], 16))
                        i += 4
                    except ValueError as e: 
                        hexed_data += data[i]
                        i += 1
                else:
                    hexed_data += data[i]
                    i += 1
            data = hexed_data

	with open(tmp_file, "wb") as f:
            f.write(data)

        fd_stdio = gdb.execute('p $fd_stdio', to_string=True)
        if 'void' in fd_stdio or '0xffff' in fd_stdio:
            tmp = gdb.execute('call (int)dup(0)', to_string=True)
            fd_stdio = int(tmp.split('=')[-1].strip().lstrip('0x'), 16)
            gdb.execute('set $fd_stdio=%d' % fd_stdio)
        gdb.execute('call (int)close(0)', to_string=True)
        gdb.execute('call (int)open("%s", 2)' % tmp_file, to_string=True)
        gdb.execute('set $cur_stdio_file=0')  # reset the var, or will get "Too many array elements" 
        gdb.execute('set $cur_stdio_file="%s"' % tmp_file)
        msg("data: " + repr(data))
        msg("set program STDIO to %s" % tmp_file)

    def file(self, *arg):
        '''
        Set stdio of the program to the FILE
        Usage:
            pstdio file [FILE]
        '''

        if len(arg) == 0:
            self.help("file")
            return
        filename = arg[0]
        if os.path.isfile(filename):
            fd_stdio = gdb.execute('p $fd_stdio', to_string=True)
            if 'void' in fd_stdio or '0xffff' in fd_stdio:
                tmp = gdb.execute('call (int)dup(0)', to_string=True)
                fd_stdio = int(tmp.split('=')[-1].strip().lstrip('0x'), 16)
                gdb.execute('set $fd_stdio=%d' % fd_stdio)
            filename = os.path.abspath(filename)
            gdb.execute('call (int)close(0)', to_string=True)
            gdb.execute('call (int)open("%s", 2)' % filename, to_string=True)
            gdb.execute('set $cur_stdio_file=0')  # reset the var, or will get "Too many array elements" 
            gdb.execute('set $cur_stdio_file="%s"' % filename)
            msg("Set program STDIO to %s" % filename)
        else:
            msg('File "%s" is not exist' % filename)

    def status(self, *arg):
        '''
        Display the status of program stdio
        Usage:
            pstdio status
        '''

        cur_stdio_file = gdb.execute('p $cur_stdio_file', to_string=True)
        if 'void' in cur_stdio_file:
            cur_stdio_file = '<stdio>'
        else:
            cur_stdio_file = cur_stdio_file.split('=')[-1].strip().strip('"')
        msg('The current stdio is "%s"' %cur_stdio_file)

    def reset(self, *arg):
        '''
        Reset stdio of program
        Usage:
            pstdio reset
        '''

        fd_stdio = gdb.execute('p $fd_stdio', to_string=True)
        if 'void' not in fd_stdio or '0xffff' not in fd_stdio:
            fd_stdio = int(fd_stdio.split('=')[-1].strip().lstrip('0x'), 16)
            gdb.execute('call (int)close(0)', to_string=True)
            gdb.execute('call (int)dup2(%d, 0)' % fd_stdio, to_string=True)
            gdb.execute('call (int)close(%d)' % fd_stdio, to_string=True)
            gdb.execute('set $fd_stdio=%d' % -1)
            gdb.execute('set $cur_stdio_file=0') 
            gdb.execute('set $cur_stdio_file="<stdio>"')

    def help(self, *arg):
        '''
        Print help text
        Usage:
            pstdio help
        '''

        (cmd,) = normalize_argv(arg, 1)
        helptext = ""
        if cmd is None:
            helptext = 'Set stdio of the program.\n'
            helptext += 'List of "pstdio" subcommands, type the subcommand to invoke it:\n'
            for cmd in self.commands:
                if cmd.startswith("_"): continue
                func = getattr(self, cmd)
                helptext += "%s -- %s\n" % (cmd, trim(func.__doc__.strip("\n").splitlines()[0]))
        else:
            if cmd in self.commands:
                func = getattr(self, cmd)
                lines = trim(func.__doc__).splitlines()
                helptext += lines[0] + "\n"
                for line in lines[1:]:
                    helptext += line + "\n"
            else:
                for c in self.commands:
                    if not c.startswith("_") and cmd in c:
                        func = getattr(self, c)
                        helptext += "%s -- %s\n" % (c, trim(func.__doc__.strip("\n").splitlines()[0]))

        msg(helptext)


class PstdioCommand(gdb.Command):
    """Set stdio of the program"""

    def __init__(self):
        super(self.__class__, self).__init__("pstdio", gdb.COMMAND_DATA)

    def invoke(self, arg_string, from_tty):
        # do not repeat command
        self.dont_repeat()
        argv = gdb.string_to_argv(arg_string)
        if len(argv) < 1:
            pstdio.help()
        else:
            cmd = argv[0]
            if cmd in pstdio.commands:
                func = getattr(pstdio, cmd)
                try:
                    func(*argv[1:])
                except Exception as e:
                    msg("Exception: %s" %e)
                    import traceback
                    traceback.print_exc()
                    pstdio.help(cmd)
            else:
                msg('Undefined Command: %s. Try "pstdio help"' % cmd)
        return

    def complete(self, text, word):
        completion = []
        cmd = text.split()[0]
        if text != "" and cmd not in pstdio.commands:
            for cmd in pstdio.commands:
                if cmd.startswith(text.strip()):
                    completion += [cmd]
        return completion


pstdio = Pstdio()
PstdioCommand()

# reset variables
def exit_handler(event):
    gdb.execute('set $fd_stdio=%d' % -1)
    gdb.execute('set $cur_stdio_file=0')
    gdb.execute('set $cur_stdio_file="<stdio>"')

gdb.events.exited.connect(exit_handler)
