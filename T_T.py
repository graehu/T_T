import re
import os
import sys
import json
import time
import zlib
import fnmatch
import tkinter as tk
import tkinter.font as tkfont

class Py:
    keyword   = r"\b(?P<keyword>False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
    exception = r"([^.'\"\\#]\b|^)(?P<exception>ArithmeticError|AssertionError|AttributeError|BaseException|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EnvironmentError|Exception|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError)\b"
    builtin   = r"([^.'\"\\#]\b|^)(?P<builtin>abs|all|any|ascii|bin|breakpoint|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dir|divmod|enumerate|eval|exec|exit|filter|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|isinstance|issubclass|iter|len|license|locals|map|max|memoryview|min|next|oct|open|ord|pow|print|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|sum|type|vars|zip)\b"
    docstring = r"(?P<docstring>(?i:r|u|f|fr|rf|b|br|rb)?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?|(?i:r|u|f|fr|rf|b|br|rb)?\"\"\"[^\"\\]*((\\.|\"(?!\"\"))[^\"\\]*)*(\"\"\")?)"
    string    = r"(?P<string>(?i:r|u|f|fr|rf|b|br|rb)?'[^'\\\n]*(\\.[^'\\\n]*)*'?|(?i:r|u|f|fr|rf|b|br|rb)?\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
    types     = r"\b(?P<types>bool|bytearray|bytes|dict|float|int|list|str|tuple|object)\b"
    number    = r"\b(?P<number>((0x|0b|0o|#)[\da-fA-F]+)|((\d*\.)?\d+))\b"
    classdef  = r"(?<=\bclass)[ \t]+(?P<classdef>\w+)[ \t]*[:\(]" #recolor of DEFINITION for class definitions
    decorator = r"(^[ \t]*(?P<decorator>@[\w\d\.]+))"
    instance  = r"\b(?P<instance>super|self|cls)\b"
    comment   = r"(?P<comment>#[^\n]*)"
    sync      = r"(?P<sync>\n)"
    regex      = rf"{keyword}|{builtin}|{exception}|{types}|{comment}|{docstring}|{string}|{sync}|{instance}|{decorator}|{number}|{classdef}"


class EventText(tk.Text):
    event_args = None
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = ""
        try:
            result = self.tk.call(cmd)
            if debug_output: print(cmd)
            if command in ("insert", "delete", "replace"):
                self.event_args = args
                self.event_generate("<<TextModified>>")

            if command in ("yview", "xview"):
                self.event_generate("<<ViewUpdated>>")
        except Exception as e:
            print(e)

        return result


_T_T_icon = zlib.decompress(b'x\x9c\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\x02 \xcc\xc1\x06$\xe5?\xffO\x04R\x8c\xc5A\xeeN\x0c\xeb\xce\xc9\xbc\x04rX\xd2\x1d}\x1d\x19\x186\xf6s\xffId\x05\xf29\x0b<"\x8b\x19\x18\xc4TA\x98\xd13H\xe5\x03P\xd0\xce\xd3\xc51\xc4\xc2?\xf9\x87\xbf\xa2\x84\x1f\x9b\x81\x81\x81\xc2\x86\xab,+4x\xee\x1c\xd3\xec\x7f\xd4\x94\x9b)\xc0\xba\x83\xc1\xec\xe7\xc34\x06K\x86v\xc6\xdb\x07\xcc\x14\x93c\x1a\xc2\xf4\x14\xe4x*\x99\xff\xfdgg\xe8\xb9\xb8\xa9\xf3\xfa\x8e\x1f\xf9@\x93\x18<]\xfd\\\xd69%4\x01\x00 >/\xb2')
_T_T_dir = os.path.expanduser("~/.T_T")
_T_T_dir = _T_T_dir.replace("\\", "/")
os.makedirs(_T_T_dir, exist_ok=True)
conf_path = "/".join((_T_T_dir, "config.json"))
config = {
    "text": {
        "foreground": "#C0C0C0",
        "background": "#252525",
        "font": ["Courier", "12"],
        "selectforeground": "#C0C0C0",
        "selectbackground": "#404040",
        "insertbackground": "#C0C0C0",
    },
    "tags":{
        "keyword": {"foreground":"#FF80FF"},
        "exception": {"foreground":"#880000"},
        "builtin": {"foreground":"#FFD700"},
        "docstring": {"foreground":"#008000"},
        "string": {"foreground":"#CC8300"},
        "types": {"foreground":"#FFD700"},
        "number": {"foreground":"#FFFFFF"},
        "classdef": {"foreground":"#8080FF"},
        "decorator": {"foreground":"#FF00FF"},
        "comment": {"foreground":"#008000"}
    }
}


files = {}
commands = {}
op_args = {}
tab_spaces = 4
current_file = ""
debug_output = False
is_fullscreen = False
editor = complist = separator = root = None
if not os.path.exists(conf_path): json.dump(config, open(conf_path, "w"), indent=4)
re_tags = re.compile(Py.regex, re.S)
br_pat = re.compile(r"}|{|\.|:|/|\"|\\|\+|\-| |\(|\)|\[|\]")



def apply_config():
    config = json.loads(open(conf_path).read())
    text_config = config["text"]
    tags_config = config["tags"]
    font, fontsize = text_config["font"] if "font" in text_config else ""
    font = font if font in tkfont.families() else "Courier"
    font = (font, fontsize)
    if not "font" in text_config: text_config["font"] = font
    text_config.update({"font":font, "relief": "flat", "borderwidth":0})
    editor.configure(inactiveselectbackground=text_config["selectbackground"], **text_config)
    palette.configure(highlightthickness=0, **text_config)
    complist.configure(highlightcolor=text_config["foreground"], **{"foreground": text_config["foreground"], "background": text_config["background"], "font":font})
    separator.configure(bg=text_config["foreground"])
    for k in editor.tag_names(): editor.tag_delete(k)
    for k in tags_config: editor.tag_configure(k, tags_config[k])
    update_tags(editor)


def get_common_path(paths):
    if len(paths) == 1: common = os.path.dirname(paths[0])
    else: common = os.path.commonpath(paths)
    if not common.endswith(os.path.sep): common += os.path.sep
    return common

def list_path(path):
    if path == os.curdir: return os.listdir(path)
    else: return [os.path.join(path, p) for p in os.listdir(path)]


def file_to_key(path): return os.path.abspath(path).replace("\\", "/").lower()

def file_set(path, data):
    global files
    key = file_to_key(path)
    assert key in files, f"'{path}' is not in files"
    files[key].update({"data": data})


def file_get(path):
    global files
    key = os.path.abspath(path).replace("\\", "/").lower()
    if key in files:
        print("getting: "+key)
        return files[key]
    name = "file"
    data = ""
    ext = ".txt"
    mtime = time.time()
    if path and os.path.exists(path):
        name, ext = os.path.splitext(path)
        name = os.path.basename(name)
        mtime = os.path.getmtime(path)
        data = open(path).read()

    file_info = {"path":path, "name": name, "data":data, "mtime":mtime, "ext":ext}
    print("adding: "+key)
    files[key] = file_info
    return file_info


def set_debug(enabled):
    global debug_output
    debug_output = enabled


def save_file(path):
    with open(path, "w") as output_file:
        text = editor.get(1.0, tk.END)
        output_file.write(text)
    if path == conf_path: apply_config()


def file_open(path):
    global root
    global current_file
    path = os.path.expanduser(path)
    path = os.path.abspath(path).replace("\\", "/")
    if current_file: file_set(current_file, editor.get("1.0", tk.END))
    current_file = path
    editor.delete(1.0, tk.END)
    file_info = file_get(current_file)
    editor.insert(tk.END, file_info["data"])
    root.title(file_info["name"])
    editor.focus_set()
    editor.mark_set(tk.INSERT, "1.0")


def get_next_break(widget, backwards=True):
    cursor = widget.index(tk.INSERT)
    line = text = None
    delta = -1 if backwards else 1
    if not isinstance(cursor, int):
        line, cursor = map(int, cursor.split("."))
        text = widget.get(f"{line}.0", f"{line}.end")
    else:
        text = widget.get()

    if len(text) > cursor+delta and cursor+delta >= 0:
        delta = 0
        matches = br_pat.finditer(text,*(0, cursor) if backwards else (cursor,))
        if match := next(matches, None):
            if backwards and (matches := list(matches)): match = matches[-1]
            group = match.group()
            stride = -len(group) if backwards else len(group)
            delta = match.span()[backwards]-cursor
            if delta == 0:
                while cursor+delta+stride >= 0 and cursor+delta+stride < len(text):
                    delta = delta+stride
                    args = (cursor+delta, cursor+delta+stride)
                    if backwards: args = args[::-1]
                    if not text.startswith(group, *args): break

        if delta == 0: delta = -cursor if backwards else len(text)-cursor
        if delta == 0: -1 if backwards else 1

    return (line, cursor, delta)


def goto_next_break(widget, backwards=True, select=False):
    line, cursor, delta = get_next_break(widget, backwards)
    start = f"{line}.{cursor}" if line else cursor
    end = f"{line}.{cursor} + {delta}c" if line else cursor+end
    if select:
        if widget.tag_ranges(tk.SEL):
            anchor = widget.index("tk::anchor1")
            old_range, new_range   = (start, anchor), (end, anchor)
            old_range = old_range if widget.compare(old_range[0],"<=",old_range[1]) else old_range[::-1]
            new_range = new_range if widget.compare(new_range[0],"<=",new_range[1]) else new_range[::-1]
            widget.tag_remove(tk.SEL, *old_range)
            widget.tag_add(tk.SEL, *new_range)
        else:
            args = (end, widget.index(tk.INSERT))
            args = args if widget.compare(args[0],"<=",args[1]) else args[::-1]
            widget.tag_add(tk.SEL, *args)
            if backwards: widget.mark_set("tk::anchor1", args[1])
            else: widget.mark_set("tk::anchor1", args[0])

    widget.mark_set(tk.INSERT, end)
    widget.see(end)
    return "break"


def delete_to_break(widget, backwards=True):
    line, cursor, delta = get_next_break(widget, backwards)
    args = (f"{line}.{cursor}", f"{line}.{cursor} + {delta}c") if line else (cursor, cursor+delta)
    if backwards: args = args[::-1]
    widget.delete(*args)
    return "break"


def editor_select_all(event=None):
    editor.tag_add(tk.SEL, "1.0", tk.END)
    editor.mark_set(tk.INSERT, "1.0")
    editor.mark_set("tk::anchor1", tk.END)
    editor.see(tk.INSERT)
    return "break"


def editor_find_text(text, backwards = False):
    forward = not backwards
    if text:
        start = editor.index(tk.INSERT)
        stop = (tk.END if forward else "1.0")
        if not forward: start += f"- {len(text)}c"
        pos = editor.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop)
        if not pos:
            start = "1.0" if forward else tk.END
            pos = editor.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop)

        if pos:
            editor.tag_remove(tk.SEL, "1.0", tk.END)
            end_pos = f"{pos}+{len(text)}c"
            editor.tag_add(tk.SEL, pos, end_pos)
            editor.mark_set(tk.INSERT, end_pos)
            editor.mark_set("tk::anchor1", pos)
            editor.see(tk.INSERT)
    return "break"


def update_tags(text: tk.Text, start="1.0", end=tk.END):
    for tag in text.tag_names():
        if tag in [tk.SEL]: continue
        text.tag_remove(tag, start, end)

    for match in re_tags.finditer(text.get(start, end)):
        groups = {k:v for k,v in match.groupdict().items() if v}
        for k in groups:
            sp_start, sp_end = match.span(k)
            sp_start = f"{start} + {sp_start}c"
            sp_end = f"{start} + {sp_end}c"
            text.tag_add(k, sp_start, sp_end)


def editor_modified(event=None):
    args = editor.event_args
    start = end = editor.index(tk.INSERT)
    line, _ = map(int, start.split("."))

    if len(args) > 1:
        start = f"{line-1}.{0}"
        start += f" - {len(args[-1])}c"
        start = editor.index(start)
        start = f"{start.split('.')[0]}.0"
        end = f"{line+1}.{0}"
    else:
        start = f"{line-1}.{0}"
        end = f"{line+1}.{0}"

    update_tags(editor, start, end)


def insert_tab(widget):
    cursor = widget.index(tk.INSERT)
    if not isinstance(cursor, int):
        _, char = map(int, cursor.split('.'))
    else: char = cursor
    widget.insert(tk.INSERT, " " * (tab_spaces-char%tab_spaces))
    return "break"


def backspace(widget):
    cursor = widget.index(tk.INSERT)
    if not isinstance(cursor, int):
        line, char = map(int, cursor.split('.'))
        if char > 0 and char % tab_spaces == 0:
            text = widget.get(f"{line}.{char-tab_spaces}", f"{line}.{char}")
            if text == " " * tab_spaces:
                widget.delete(f"{line}.{char-tab_spaces}", f"{line}.{char}")
                return "break"
    return None


# -----------------------------------------------------

def palette_command(text, shift=False):
    if ": " in text:
        cmd, text = text.split(": ", maxsplit=1)
        if cmd in commands:
            commands[cmd]["command"]((text, shift))


def palette_op(op=None):
    text = palette.get()
    index = text.find(":")
    if index != -1: old_op, old_args = text.split(":", maxsplit=1); op_args[old_op] = old_args
    palette.delete(0,tk.END)
    if op: palette.insert(0, op+":"+(op_args[op] if op in op_args else " "))
    palette_select_all()
    palette.focus_set()
    palette.bind("<Return>", lambda x: palette_command(palette.get()))
    palette.bind("<Shift-Return>", lambda x: palette_command(palette.get(), True))
    return "break"


def palette_select_all(event=None):
    complist_update(palette.get())
    text = palette.get()
    index = text.find(":")
    if index != -1: palette.selection_range(index+2, tk.END)
    else: palette.selection_range(0, tk.END)
    return "break"

# -----------------------------------------------------

def complist_update(text):
    complist.delete(0, tk.END)
    width = 0; height = 0
    if ": " in text:
        cmd, text = text.split(": ", maxsplit=1)
        if cmd in commands and "match_cb" in commands[cmd]:
            matches = commands[cmd]["match_cb"](text)
            for match in matches: complist.insert(tk.END, match)
            height = complist.size()
            width = len(max(matches, key=len))+1 if height else 0
    complist.config(height=height, width=width)
    complist.place(x=palette.winfo_x(), y=palette.winfo_y()+height) # hack to force complist_configured


def complist_configured(event=None):
    global complist
    if complist:
        complist.place_forget()
        if complist.size() != 0:
            height = complist.winfo_height()
            complist.place(x=palette.winfo_x(), y=palette.winfo_y()-height)


def complist_insert(event=None, sel=-1):
    if complist.size() == 0: return "break"
    if sel == -1: sel = complist.curselection()
    if sel != None and sel != -1:
        cmd = palette.get()
        if ":" in cmd: cmd = cmd[:cmd.index(":")]+": "
        else: cmd = ""
        palette.delete(0, tk.END)
        selected_text = complist.get(sel)
        palette.insert(0, cmd+selected_text)
        palette.focus_set()
    return "break"

# -----------------------------------------------------

def cmd_open_matches(text):
    low_text = text.lower()
    dirname, basename = os.path.split(low_text)
    ret = []
    def file_filter(word):
        if len(low_text) >= len(word): return False
        low_word = word.lower()
        base_word = low_word.replace(dirname, "")
        return (basename in base_word) or (fnmatch.fnmatch(low_word, low_text))
    path = os.path.dirname(text)
    expanded = os.path.expanduser(path)
    if expanded and (os.path.exists(expanded)): ret = list_path(expanded)
    else: ret = list_path(os.curdir)
    return list(filter(file_filter, ret))


def cmd_file_matches(text):
    low_text = text.lower()
    dirname, basename = os.path.split(low_text)
    def file_filter(word):
        if len(low_text) >= len(word): return False
        low_word = word.lower()
        base_word = low_word.replace(dirname, "")
        return (basename in base_word) or (fnmatch.fnmatch(low_word, low_text))
    paths = [files[p]["path"] for p in files.keys()]
    paths.remove(current_file)
    if paths:
        common = get_common_path(paths)
        return list(filter(file_filter, [p.replace(common, '', 1) for p in paths]))
    return []


def cmd_exec(text):
    try: exec(text, globals(), locals())
    except Exception as e: print(e)


def cmd_file(text):
    paths = [files[p]["path"] for p in files.keys()]
    paths.remove(current_file)
    path = os.path.join(get_common_path(paths), text)
    file_open(path)


def cmd_register(name, command, match_cb=None, shortcut=None):
    global commands
    assert not name in commands, f"'{name}' already registered "
    cmd = {"command": command}
    if match_cb: cmd.update({"match_cb": match_cb})
    if shortcut:
        root.bind(shortcut, lambda x: palette_op(name))
        editor.bind(shortcut, lambda x: palette_op(name))
    commands[name] = cmd

# -----------------------------------------------------

def fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes("-fullscreen", is_fullscreen)


if os.name == "nt":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

root = tk.Tk()
if os.name == "nt": root.title("")
else: root.title("T_T")


photo = tk.PhotoImage(data=_T_T_icon)
root.wm_iconphoto(False, photo)

root.bind("<Control-p>", lambda x: palette_op())
root.bind("<Control-s>", lambda x: save_file(current_file))
root.bind("<Control-w>", lambda x: root.quit())
root.bind("<Configure>", lambda x: complist_configured())
root.bind("<Control-m>", lambda _: file_open(conf_path))

editor = EventText(root, highlightthickness=0, wrap='none', height=30, width=80, undo=True)
editor.selection_own()
editor.bind("<<TextModified>>", editor_modified)
editor.bind("<Control-a>", editor_select_all)
editor.bind("<Control-Left>", lambda x: goto_next_break(editor))
editor.bind("<Control-Right>", lambda x: goto_next_break(editor, False))
editor.bind("<Control-Shift-Left>", lambda x: goto_next_break(editor, True, True))
editor.bind("<Control-Shift-Right>", lambda x: goto_next_break(editor, False, True))
editor.bind("<Control-BackSpace>", lambda x: delete_to_break(editor))
editor.bind("<Control-Delete>", lambda x: delete_to_break(editor, False))
editor.bind("<BackSpace>", lambda x: backspace(editor))
editor.bind("<FocusIn>", lambda x: complist.place_forget())
editor.bind("<Tab>", lambda x: insert_tab(editor))
editor.bind("<Control-p>", lambda x: palette_op())

editor.pack(expand=True, fill="both")

separator = tk.Frame(root, height=1, bd=0)
separator.pack(fill="x", expand=False)

complist = tk.Listbox(root, relief='flat')
complist.bind("<Double-Button-1>", complist_insert)
complist.bind("<Return>", complist_insert)
complist.bind("<Tab>", complist_insert)
complist.bind("<Configure>", complist_configured)
complist.bind("<Escape>", lambda x: palette.focus_set())

palette = tk.Entry(root, width=60)
palette.bind("<Control-a>", palette_select_all)
palette.bind("<KeyRelease>", lambda x: complist_update(palette.get()))
palette.bind('<FocusIn>', lambda x: palette.focus_set())
palette.bind("<Control-BackSpace>", lambda x: delete_to_break(palette))
palette.bind("<Control-Delete>", lambda x: delete_to_break(palette, False))
palette.bind("<Escape>", lambda x: editor.focus_set())
palette.bind("<Tab>", lambda x: complist_insert(None, 0))
palette.bind("<Down>", lambda x: (complist.focus_set(), complist.select_set(0)) if complist.size() else "")

cmd_register("open", lambda x: file_open(x[0]), cmd_open_matches, "<Control-o>")
cmd_register("file", lambda x: cmd_file(x[0]), cmd_file_matches, "<Control-t>")
cmd_register("find", lambda x: editor_find_text(*x), shortcut="<Control-f>")
cmd_register("exec", lambda x: cmd_exec(x[0]), shortcut="<Control-e>")

palette.pack(fill="x")
apply_config()

if sys.argv[1:] and os.path.exists(sys.argv[1]): file_open(sys.argv[1])
else:
    new_file = "new_file.txt"
    for i in range(0, 1000):
        if not os.path.exists(new_file): break
        new_file = f"new_file{i}.txt"
    file_open(new_file)

root.mainloop()
