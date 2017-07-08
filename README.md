# pstdio
A GDB plug-in that can set stdio of the program you debug

# Installation
```
git clone https://github.com/Ovi3/pstdio.git ~/pstdio
echo "source ~/pstdio/pstdio.py" >> ~/.gdbinit
```

# Usage

First open GDB, And type 'pstdio help' to see the help text.

Example:
1. When you debug the program, and the program will call the '`<read@plt>` to read data from stdio.
2. And if you wanna enter the data, like '\x02\x03\x04\x05', just type:
```
pstdio data /x \\x02\\x03\\x04\\x05
```
3. Then execute the 'call `<read@plt>`', the data you enter will be input.
4. Or you can type 'psdtio file /path/to/data'. In the case, data of the file will bu input.
