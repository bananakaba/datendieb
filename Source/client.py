from pathlib import Path
import platform
from datetime import datetime

# prefix components:
space =  '    '
branch = '│   '
# pointers:
tee =    '├── '
last =   '└── '


def tree(dir_path: Path, prefix: str=''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """ 
    try:   
        contents = [file for file in dir_path.iterdir() if not file.name.startswith(".")]
        # contents each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            yield prefix + pointer + path.name
            if path.is_dir(): # extend the prefix and recurse:
                extension = branch if pointer == tee else space 
                # i.e. space because last, └── , above so no more |
                yield from tree(path, prefix=prefix+extension)
    except PermissionError: # skip folders with no reading permission
        pass

def filetype(dir_path: Path, prefix: str=''):
    try:
        file = [file for file in dir_path.iterdir() if not file.name.startswith(".")]
        for path in file:
            yield path
            if path.is_dir(): # extend the prefix and recurse:
                yield from filetype(path, prefix=prefix)
    except PermissionError:
        pass

try:
    if platform.system() == "Linux":
        f = open("Source/data/" + datetime.now().strftime("%d_%m_%Y"),"w")
        for line in tree(Path.home() / "/home/"):
            #print(line)
            f.write(line + "\n")
        f.close()

        files_dict = {}
        for i in filetype(Path.home() / "/home/"):
            if i.is_file():
                files_dict.update({i.name: i.stat().st_size})
        ordered = {k: v for k, v in sorted(files_dict.items(), key=lambda item: item[1], reverse=True)}
        f = open("Source/data/" + "files_" + datetime.now().strftime("%d_%m_%Y"),"w")
        for x, y in ordered.items():
            f.write(x + "   " + str(y) + "\n")
        f.close()
        
    if platform.system() == "Windows":
        f = open("Source/data/" + datetime.now().strftime("%d_%m_%Y"),"w")
        for line in tree(Path.home()):
            #print(line)
            f.write(line + "\n")
        f.close()

        files_dict = {}
        for i in filetype(Path.home()):
            if i.is_file():
                files_dict.update({i.name: i.stat().st_size})
        ordered = {k: v for k, v in sorted(files_dict.items(), key=lambda item: item[1], reverse=True)}
        f = open("Source/data/" + "files_" + datetime.now().strftime("%d_%m_%Y"),"w")
        for x, y in ordered.items():
            f.write(x + "   " + str(y) + "\n")
        f.close()
    
except KeyboardInterrupt:
    f.close()