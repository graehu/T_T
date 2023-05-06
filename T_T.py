import re
import os
import json
import zlib
import fnmatch
import tkinter as tk
import tkinter.font as tkfont

_T_T_icon = zlib.decompress(b'x\x9c\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\x02 \xcc\xc1\x06$\xe5?\xffO\x04R\x8c\xc5A\xeeN\x0c\xeb\xce\xc9\xbc\x04rX\xd2\x1d}\x1d\x19\x186\xf6s\xffId\x05\xf29\x0b<"\x8b\x19\x18\xc4TA\x98\xd13H\xe5\x03P\xd0\xce\xd3\xc51\xc4\xc2?\xf9\x87\xbf\xa2\x84\x1f\x9b\x81\x81\x81\xc2\x86\xab,+4x\xee\x1c\xd3\xec\x7f\xd4\x94\x9b)\xc0\xba\x83\xc1\xec\xe7\xc34\x06K\x86v\xc6\xdb\x07\xcc\x14\x93c\x1a\xc2\xf4\x14\xe4x*\x99\xff\xfdgg\xe8\xb9\xb8\xa9\xf3\xfa\x8e\x1f\xf9@\x93\x18<]\xfd\\\xd69%4\x01\x00 >/\xb2')
_T_T_dir = os.path.expanduser("~/.T_T")
_T_T_dir = _T_T_dir.replace("\\", "/")
conf_path = "/".join((_T_T_dir, "config.json"))
config = {
    "theme":{
        "fg": "#C0C0C0",
        "bg": "#252525",
        "selected": "#404040",
        "syntax": {
            "keyword": "#FF80FF",
            "exception": "#880000",
            "builtin": "#FFD700",
            "docstring": "#008000",
            "string": "#CC8300",
            "types": "#FFD700",
            "number": "#FFFFFF",
            "classdef": "#8080FF",
            "decorator": "#FF00FF",
            "comment": "#008000"
        }
    }
}

os.makedirs(_T_T_dir, exist_ok=True)
def save_config(): json.dump(config, open(conf_path, "w"), indent=4)
def open_config(): open_file(conf_path)
if not os.path.exists(conf_path): save_config()
config = json.load(open(conf_path))
debug_output = False

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


re_tags = re.compile(Py.regex, re.S)

def set_debug(enabled):
    global debug_output
    debug_output = enabled

class EventText(tk.Text):
    event_args = None
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
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


current_file_path = None
def save_file(path):
    with open(path, "w") as output_file:
        text = editor.get(1.0, tk.END)
        output_file.write(text)


def open_file(file_path):
    global root
    global current_file_path
    file_path = os.path.expanduser(file_path)
    file_path = os.path.abspath(file_path)
    if os.path.exists(file_path):
        current_file_path = file_path
        editor.delete(1.0, tk.END)
        with open(current_file_path, "r") as input_file:
            text = input_file.read()
            editor.insert(tk.END, text)
        root.title(current_file_path)
        editor.focus_set()
        editor.mark_set(tk.INSERT, "1.0")


def delete_word_backwords(widget):
    cursor = widget.index(tk.INSERT)
    start = cursor
    if not isinstance(cursor, int):
        while start != "1.0":
            wordstart = widget.index(f"{start} wordstart")
            if wordstart == start:
                start = widget.index(start +" - 1c")
            elif cursor.split('.')[0] != wordstart.split('.')[0]:
                start = f"{cursor.split('.')[0]}.0"
                break
            else:
                start = f"{wordstart}"
                break
    else:
         text = widget.get()
         while start != 0:
            start -= 1
            if text[start] == " ":
                start +=1
                break
    if start != cursor:
        widget.delete(f"{start}", cursor)
        return "break"
    return None


br_pat = re.compile(r"}|{|\.|:|/|\"|\\|\+|\-| |\(|\)|\[|\]")
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


def editor_find_text(text, forward = True):
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


def palette_command(text, shift=False):
    if text.startswith("find: "): editor_find_text(text[len("find: "):], not shift)
    elif text.startswith("open: "): open_file(text[len("open: "):])
    elif text.startswith("config: "): open_config()
    elif text.startswith("exec: "):
        try:
            exec(text[len("exec: "):], globals(), locals())
        except Exception as e:
            print(e)
    else:
        print(text)


op_args = {}
def palette_op(op=None):
    text = palette.get()
    index = text.find(":")
    if index != -1: old_op, old_args = text.split(":", maxsplit=1); op_args[old_op] = old_args
    palette.delete(0,tk.END)
    if op: palette.insert(0, op+":"+(op_args[op] if op in op_args else " "))
    palette_select_all()
    palette.focus_set()
    palette.bind("<Return>", lambda event: palette_command(palette.get()))
    palette.bind("<Shift-Return>", lambda event: palette_command(palette.get(), True))
    return "break"


def palette_select_all(event=None):
    complist_update(palette.get())
    text = palette.get()
    index = text.find(":")
    if index != -1: palette.selection_range(index+2, tk.END)
    else: palette.selection_range(0, tk.END)
    return "break"


def complist_get_completions(text):
    if text.startswith("open: "):
        path = text[len("open: "):]
        path = os.path.dirname(path)
        expanded = os.path.expanduser(path)
        if path and not expanded.endswith("/"): expanded += "/"
        if expanded and (os.path.exists(expanded)):
            if not path.endswith("/"): path += "/"
            return [f"open: "+path+p+("/" if os.path.isdir(expanded+p)else"") for p in os.listdir(expanded)]
        else:
            return [f"open: "+p+("/" if os.path.isdir(p) else "") for p in os.listdir(".")]
    return commands


def complist_get_match_func(text):
    low_text = text.lower()
    def open_match(word):
        nonlocal low_text
        if len(text) >= len(word): return False
        word_low = word.lower()
        return low_text in word_low or fnmatch.fnmatch(word_low, low_text)
    if text.startswith("open: "): return open_match
    return lambda x: len(text) < len(x) and x.startswith(low_text)


def complist_update(text):
    comps = complist_get_completions(text)
    match_func = complist_get_match_func(text)
    matches = [word for word in comps if match_func(word)] if text else []
    complist.delete(0, tk.END)
    for match in matches: complist.insert(tk.END, match)
    height = len(matches)
    width = len(max(matches, key=len))+1 if height else 0
    complist.config(height=height, width=width)
    complist.place(x=palette.winfo_x(), y=palette.winfo_y()+height) # hack to force complist_configured


def complist_configured(event=None):
    complist.place_forget()
    if complist.size() != 0:
        height = complist.winfo_height()
        complist.place(x=palette.winfo_x(), y=palette.winfo_y()-height)


def complist_insert(event=None, sel=-1):
    if complist.size() == 0: return "break"
    if sel == -1: sel = complist.curselection()
    if sel != None and sel != -1:
        selected_text = complist.get(sel)
        palette.delete(0, tk.END)
        text = palette.get()
        index = text.find(":")
        if index != -1: palette.selection_range(index+2, tk.END)
        else: palette.selection_range(0, tk.END)
        palette.insert(0, selected_text)
        palette.focus_set()
    return "break"

is_fullscreen = False
def fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes("-fullscreen", is_fullscreen)

if os.name == "nt":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

root = tk.Tk()
if os.name == "nt":
    root.title("")
else:    
    root.title("T_T")

photo = tk.PhotoImage(data=_T_T_icon)
root.wm_iconphoto(False, photo)


root.bind("<Control-f>", lambda x: palette_op("find"))
root.bind("<Control-o>", lambda x: palette_op("open"))
root.bind("<Control-e>", lambda x: palette_op("exec"))
root.bind("<Control-m>", lambda x: palette_op("config"))
root.bind("<Control-p>", lambda x: palette_op())
root.bind("<Control-s>", lambda x: save_file(current_file_path))
root.bind("<Control-w>", lambda x: root.quit())
root.bind("<Configure>", lambda x: complist_configured())


font = config["theme"]["font"] if "font" in config["theme"] else ""
fonts = [font, "Inconsolata", "Fira Mono", "Source Code Pro", "Anonymous Pro", "M+ 1M", "Hack", "Monolisa", "Gintronic", "Droid Sans Mono", "Dank Mono", "PragmataPro", "DejaVu Sans Mono", "Ubuntu Mono", "Bitstream Vera Sans Mono"]
font = next((f for f in fonts if f in tkfont.families()), "Courier")
fontsize = config["theme"]["fontsize"] if "fontsize" in config["theme"] else 12
font = (font, fontsize)
if not "font" in config["theme"]: config["theme"]["font"] = font[0]
if not "fontsize" in config["theme"]: config["theme"]["fontsize"] = font[1]

text_config = {"relief": "flat", "borderwidth":0, "fg": config["theme"]["fg"], "bg": config["theme"]["bg"], "font":font, "insertbackground": config["theme"]["fg"]}
editor = EventText(root, highlightthickness=0, inactiveselectbackground=config["theme"]["selected"], wrap='none', height=30, width=60, undo=True, **text_config)

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

tab_spaces = 4

editor.pack(expand=True, fill="both")

tags = {}
for k in config["theme"]["syntax"]:
    tags[k] = {
        "foreground": config["theme"]["syntax"][k],
        "selectforeground": config["theme"]["syntax"][k],
        "selectbackground": config["theme"]["selected"]
        }

tags[tk.SEL] = {
    'foreground': config["theme"]["fg"],
    'background': config["theme"]["selected"],
    "selectforeground": config["theme"]["fg"],
    "selectbackground": config["theme"]["selected"]
}
for k in tags: editor.tag_configure(k, tags[k])

separator = tk.Frame(root, bg=config["theme"]["fg"], height=1, bd=0)
separator.pack(fill="x", expand=False)

complist = tk.Listbox(root, relief='flat', highlightcolor=config["theme"]["fg"], **{"foreground": config["theme"]["fg"], "background": config["theme"]["bg"], "font":font})
complist.bind("<Double-Button-1>", complist_insert)
complist.bind("<Return>", complist_insert)
complist.bind("<Tab>", complist_insert)
complist.bind("<Configure>", complist_configured)
complist.bind("<Escape>", lambda x: palette.focus_set())

palette = tk.Entry(root, width=60, **text_config, highlightthickness=0)
palette.bind("<Control-a>", palette_select_all)
palette.bind("<KeyRelease>", lambda x: complist_update(palette.get()))
palette.bind('<FocusIn>', lambda x: palette.focus_set())
palette.bind("<Control-BackSpace>", lambda x: delete_to_break(palette))
palette.bind("<Control-Delete>", lambda x: delete_to_break(palette, False))
palette.bind("<Escape>", lambda x: editor.focus_set())
palette.bind("<Tab>", lambda x: complist_insert(None, 0))
palette.bind("<Down>", lambda x: (complist.focus_set(), complist.select_set(0)) if complist.size() else "")

commands = ["open: ", "find: ", "exec: ", "config: "]

palette.pack(fill="x")

root.mainloop()
