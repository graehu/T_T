#!/usr/bin/env python3
import re, os, sys, ast, glob, json, time, zlib, fnmatch, subprocess, threading, webbrowser, pickle, shutil
import tkinter as tk
import tkinter.font as tkfont

class Generic:
    brackets  = r"(?P<brackets>[\(\)\[\]\{\}])"
    number    = r"\b(?P<number>((0x|0b|0o|#)[\da-fA-F]+)|((\d*\.)?\d+))\b"
    symbols   = r"(?P<symbols>[-\*$£&|~\?/+%^!:\.=])"
    links     = r"\b(?P<links>(file://|https?://)[^\s]*)\b"
    regex     = rf"{links}|{brackets}|{symbols}|{number}"

class Json:
    string    = r"(?P<string>\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
    regex     = rf"{string}|{Generic.symbols}|{Generic.brackets}|{Generic.number}"

class Xml:
    tag       = r"(?P<brackets><\/?(?P<xmltag>[\w]+)|>)"
    regex     = rf"{Json.string}|{Generic.symbols}|{Generic.number}|{tag}"

class Py:
    keyword   = r"\b(?P<keyword>False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
    exception = r"([^.'\"\\#]\b|^)(?P<exception>ArithmeticError|AssertionError|AttributeError|BaseException|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EnvironmentError|Exception|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError)\b"
    builtin   = r"([^.'\"\\#]\b|^)(?P<builtin>abs|all|any|ascii|bin|breakpoint|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dir|divmod|enumerate|eval|exec|exit|filter|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|isinstance|issubclass|iter|len|license|locals|map|max|memoryview|min|next|oct|open|ord|pow|print|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|sum|type|vars|zip)\b"
    docstring = r"(?P<docstring>(?i:r|u|f|fr|rf|b|br|rb)?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?|(?i:r|u|f|fr|rf|b|br|rb)?\"\"\"[^\"\\]*((\\.|\"(?!\"\"))[^\"\\]*)*(\"\"\")?)"
    string    = r"(?P<string>(?i:r|u|f|fr|rf|b|br|rb)?'[^'\\\n]*(\\.[^'\\\n]*)*'?|(?i:r|u|f|fr|rf|b|br|rb)?\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
    types     = r"\b(?P<types>bool|bytearray|bytes|dict|float|int|list|str|tuple|object)\b"
    symbols   = Generic.symbols
    brackets  = Generic.brackets
    number    = Generic.number
    classdef  = r"(?<=\bclass)[ \t]+(?P<classdef>\w+)[ \t]*[:\(]" #recolor of DEFINITION for class definitions
    decorator = r"(^[ \t]*(?P<decorator>@[\w\d\.]+))"
    instance  = r"\b(?P<instance>super|self|cls)\b"
    comment   = r"(?P<comment>#[^\n]*)"
    regex     = rf"{keyword}|{builtin}|{exception}|{types}|{symbols}|{brackets}|{comment}|{docstring}|{string}|{instance}|{decorator}|{number}|{classdef}"

re_py_tags = re.compile(Py.regex, re.S)
re_json_tags = re.compile(Json.regex, re.S)
re_xml_tags = re.compile(Xml.regex, re.S)
re_gen_tags = re.compile(Generic.regex, re.S)

class EventText(tk.Text):
    event_args = tag_regex = None
    path = name = ext = ""
    edits = extern_edits = read_only = False
    mtime = tag_line = 0
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)
        for k, v in commands.items(): self.bind(v["shortcut"], lambda _, key=k: palette_op(key))
        self.selection_own()
        def focused():
            global last_complist
            complist.place_forget()
            last_complist = ""
        self.bind("<Control-a>", lambda x: select_all(self))
        self.bind("<Control-Left>", lambda x: goto_next_break(self))
        self.bind("<Control-Right>", lambda x: goto_next_break(self, False))
        self.bind("<Control-Shift-Left>", lambda x: goto_next_break(self, True, True))
        self.bind("<Control-Shift-Right>", lambda x: goto_next_break(self, False, True))
        self.bind("<Control-BackSpace>", lambda x: delete_to_break(self))
        self.bind("<Control-Delete>", lambda x: delete_to_break(self, False))
        self.bind("<BackSpace>", lambda x: backspace(self))
        self.bind("<FocusIn>", lambda x: focused())
        self.bind("<Tab>", lambda x: insert_tab(self))
        self.bind("<Control-w>", lambda x: file_close(self.path))
        self.bind("<<TextModified>>", lambda x: editor_modified(self))
        self.bind("<Control-g>", goto_link)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = ""
        try:
            result = self.tk.call(cmd)
            if debug_output: print(cmd)
            if command in ("insert", "delete", "replace"):
                self.event_args = args
                self.event_generate("<<TextModified>>")
            # if command in ("yview", "xview"):
            #     self.event_generate("<<ViewUpdated>>")
        except Exception as e:
            print(e, file=sys.stderr)

        return result


_grampy_icon = zlib.decompress(b'x\x9c\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2\x02 \xcc\xc1\x06$\xe5?\xffO\x04R\x8c\xc5A\xeeN\x0c\xeb\xce\xc9\xbc\x04rX\xd2\x1d}\x1d\x19\x186\xf6s\xffId\x05\xf29\x0b<"\x8b\x19\x18\xc4TA\x98\xd13H\xe5\x03P\xd0\xce\xd3\xc51\xc4\xc2?\xf9\x87\xbf\xa2\x84\x1f\x9b\x81\x81\x81\xc2\x86\xab,+4x\xee\x1c\xd3\xec\x7f\xd4\x94\x9b)\xc0\xba\x83\xc1\xec\xe7\xc34\x06K\x86v\xc6\xdb\x07\xcc\x14\x93c\x1a\xc2\xf4\x14\xe4x*\x99\xff\xfdgg\xe8\xb9\xb8\xa9\xf3\xfa\x8e\x1f\xf9@\x93\x18<]\xfd\\\xd69%4\x01\x00 >/\xb2')
_grampy_dir = os.path.expanduser("~/.grampy")
_grampy_dir = _grampy_dir.replace("\\", "/")
os.makedirs(_grampy_dir, exist_ok=True)
conf_path = "/".join((_grampy_dir, "config.json"))
config = {
    "text": {
        "foreground": "gray72",
        "background": "gray16",
        "font": ["Fira Mono", 12],
        "selectforeground": "gray99",
        "selectbackground": "gray24",
        "insertbackground": "white",
        "highlightthickness": 8,
        "highlightcolor": "gray24",
        "highlightbackground": "gray20"
    },
    "tags": {
        "keyword": { "foreground": "hotpink" },
        "exception": { "foreground": "red" },
        "builtin": { "foreground": "gold" },
        "docstring": { "foreground": "skyblue" },
        "string": { "foreground": "lightgreen" },
        "symbols": { "foreground": "white" },
        "brackets": { "foreground": "skyblue" },
        "links": { "foreground": "skyblue" },
        "types": { "foreground": "white" },
        "number": { "foreground": "white" },
        "classdef": { "foreground": "skyblue" },
        "decorator": { "foreground": "gold" },
        "comment": { "foreground": "green" },
        "xmltag": { "foreground": "skyblue" }
    }
}

files = {}
commands = {}
op_args = {}
glob_map = {}
cache_name = ""
tag_line_stride = 128
tab_spaces = 4
last_complist = ""
current_file = ""
debug_output = False
is_fullscreen = False
editor = complist = root = None
destroy_list = []
start_time = time.time_ns()
match_lock = threading.Lock()
gui_lock = threading.Lock()
file_lock = threading.Lock()
_sess_dir = "/".join((_grampy_dir, str(start_time)))
os.makedirs(_sess_dir)
stdout_path = "/".join((_sess_dir, "output.log"))
sys.stdout = open(stdout_path, "w")
max_threads = 32

if not os.path.exists(conf_path): json.dump(config, open(conf_path, "w"), indent=4)
conf_mtime = os.path.getmtime(conf_path)
br_pat = re.compile(r"}|{|\.|:|/|\"|\\|\+|\-| |\(|\)|\[|\]")

def is_main_thread(): return threading.current_thread() is threading.main_thread()

def share_work(worker, in_args):
    threads = []
    available_threads = max_threads-(len(threading.enumerate())-1)
    print(f"using {available_threads} threads")
    step = int((len(in_args)/available_threads)+.5)
    while len(in_args) > step and step > 0:
        args, in_args = in_args[:step], in_args[step:]
        threads.append(threading.Thread(target=worker, args=([args]), name=worker.__name__))
    threads.append(threading.Thread(target=worker, args=([in_args]), name=worker.__name__))
    for t in threads: t.start()
    for t in threads: t.join()


def step_tags() -> bool:
    lines = int(editor.index('end-1c').split('.')[0])
    if editor.tag_line < lines:
        start, end = editor.tag_line, editor.tag_line+128
        update_tags(editor, f"{start}.0", f"{end}.0")
        editor.tag_line = end
        return True
    return False


def spawn(path):
    flags = 0
    if os.name == "nt": flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.CREATE_DEFAULT_ERROR_MODE
    if os.name != "nt": bar_height = (int(root.winfo_geometry().split("+")[-1])-int(root.wm_geometry().split("+")[-1]))-7 # TODO: workout a clean/correct way to do this.
    else: bar_height = 0
    swidth = root.winfo_screenwidth()
    geo = [root.winfo_x(), root.winfo_y(), root.winfo_width(), root.winfo_height()]
    geo[1], geo[0] = geo[1]-bar_height, geo[0]+geo[2] if ((geo[0]+(geo[2]/2))%swidth) < swidth/2 else geo[0]-geo[2]
    subprocess.Popen([sys.executable, __file__, path, f"geo={geo}"], creationflags=flags)


def apply_config(widget):
    global config
    try:
        config = json.loads(open(conf_path).read())
        text_config = config["text"]
        tags_config = config["tags"]
        font, fontsize = text_config["font"] if "font" in text_config else ""
        font = font if font in tkfont.families() else "Courier"
        font = (font, fontsize)
        if not "font" in text_config: text_config["font"] = font
        text_config.update({"font":font, "relief": "flat", "borderwidth":0})
        widget.configure(inactiveselectbackground=text_config["selectbackground"], **text_config)
        palette.configure(**text_config)
        del text_config["insertbackground"]
        complist.configure(**text_config)
        for k in widget.tag_names(): widget.tag_delete(k)
        for k in tags_config: widget.tag_configure(k, tags_config[k])
    except Exception as e:
        print(e, file=sys.stderr)


def update_title(widget):
    if widget != editor: return
    title = widget.name
    if widget.edits: title += "*"
    if widget.read_only: title += "  (read only)"
    if widget.extern_edits: title = f"!! WARNING !!    External edits to  ' {title} '  close and reopen    !! WARNING !!"
    root.title(title)


def show_stdout(): file_open(stdout_path, read_only=True); root.update()

def shorten_paths(paths):
    tails, tops = list(zip(*[os.path.split(p) for p in paths]))
    while len(set(tops)) != len(tops):
        tails, new_tops = list(zip(*[os.path.split(t) for t in tails]))
        tops = [os.path.join(t1, t2) for t1,t2 in zip(new_tops, tops)]
    return tops


def list_path(path):
    if path == os.curdir: paths = os.listdir(path)
    else: paths = [os.path.join(path, p) for p in os.listdir(path)]
    paths = [p+os.path.sep if os.path.isdir(p) else p for p in paths]
    return paths


def file_to_key(path): return os.path.abspath(path).replace("\\", "/").lower()


def goto_link(event):
    widget : EventText = event.widget
    if "links" in widget.tag_names(tk.INSERT):
        ranges = widget.tag_ranges("links")
        ranges = zip(ranges[::2], ranges[1::2])
        for x,y in ranges:
            if widget.compare(tk.INSERT, ">", x) and \
                widget.compare(tk.INSERT, "<", y):

                link = widget.get(x,y)
                if link.startswith("http://") or link.startswith("https://"):
                    webbrowser.open(widget.get(x,y))
                else:
                    path = link.split("//", maxsplit=1)[1]
                    path, *loc = path.split(":")
                    if len(loc) == 2: line,char = loc
                    elif len(loc) == 1: line = loc[0]; char = 0
                    else: line=char=0
                    paths = [files[p]["path"] for p in files.keys()]
                    paths = zip(paths, shorten_paths(paths))
                    tab_path = next((x for x, y in paths if y.endswith(path)), "")
                    if tab_path: file_open(tab_path,tindex=f"{line}.{char}")
                    elif os.path.exists(path): file_open(path)


def file_get(path, read_only=False, cache=None):
    global files
    key = file_to_key(path)
    if key in files:
        info = files.pop(key)
        if not is_main_thread(): file_lock.acquire()
        files = {**{key:info}, **files}
        if not is_main_thread(): file_lock.release()
        return info
    name = os.path.basename(path)
    _, ext = os.path.splitext(path)
    data = ""
    if not cache:
        mtime = time.time()
        if path and os.path.exists(path) and os.path.isfile(path):
            mtime = os.path.getmtime(path)
            try: data = open(path).read()
            except Exception as e: print("error: file://"+path+" - "+str(e)); return None
    else:
        data = cache; mtime = 0
    
    if not is_main_thread(): gui_lock.acquire()
    widget = EventText(root, wrap='none', undo=True, **config["text"])
    root.update()
    if not is_main_thread(): gui_lock.release()
    widget.path = path
    widget.name = name
    widget.ext = ext
    if ext in [".py", ".pyw"]: widget.tag_regex = re_py_tags
    elif ext in [".json"]: widget.tag_regex = re_json_tags
    elif ext in [".xml", ".meta"]: widget.tag_regex = re_xml_tags
    else: widget.tag_regex = re_gen_tags
    widget.mtime = mtime
    widget.insert(tk.END, data)
    if read_only: widget.mark_set(tk.INSERT, tk.END)
    else: widget.mark_set(tk.INSERT, "1.0")
    widget.edit_reset()
    widget.edits = False
    widget.read_only = read_only
    if read_only: widget.configure(state=tk.DISABLED)
    widget.edit_modified(False)
    file_info = {"path":path, "editor":widget}
    if not is_main_thread(): file_lock.acquire()
    files = {**{key:file_info}, **files}
    if not is_main_thread(): file_lock.release()
    return file_info


def file_close(path):
    global current_file
    global files
    key = file_to_key(path)
    print("close: file://"+path)
    info = files.pop(key)
    destroy_list.append(info["editor"])
    current_file = ""
    if files: file_open(next(iter(files)))
    else: root.quit()


def set_debug(enabled):
    global debug_output
    debug_output = enabled


def save_file(path):
    if not os.path.exists(path) or os.path.isfile(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as output_file:
            text = editor.get(1.0, 'end-1c')
            output_file.write(text)
            if path == current_file:
                editor.edits = False
                editor.extern_edits = False
                editor.mtime = os.path.getmtime(path)
                update_title(editor)
                editor.edit_modified(0)
            if path == conf_path: apply_config(editor)


def file_open(path, new_inst=False, read_only=False, background=False, tindex=None):
    global root
    global current_file
    global editor
    global glob_map
    glob_map = {}
    path = os.path.expanduser(path)
    path = os.path.abspath(path).replace("\\", "/")
    if os.path.isdir(path): return
    if background:
        if file_get(path, read_only) == None: return
    elif not new_inst:
        current_file = path
        editor.pack_forget()
        editor.config()
        file_info = file_get(current_file, read_only)
        editor = file_info["editor"]
        if tindex: editor.mark_set(tk.INSERT, tindex); editor.see(tk.INSERT)
        apply_config(editor)
        editor.pack(before=palette, expand=True, fill="both")
        update_title(editor)
        editor.tag_line = 1
        step_tags()
        editor.lower()
        editor.focus_set()
    elif os.path.exists(path):
        spawn(path)
    if not background: print("open: file://"+path)


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


def select_all(widget):
    widget.tag_add(tk.SEL, "1.0", tk.END)
    widget.mark_set(tk.INSERT, "1.0")
    widget.mark_set("tk::anchor1", tk.END)
    widget.see(tk.INSERT)
    return "break"


def find_text(widget, text, backwards = False):
    forward = not backwards
    if text:
        start = widget.index(tk.INSERT)
        stop = (tk.END if forward else "1.0")
        if not forward: start += f"- {len(text)}c"
        pos = widget.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop, nocase=True)
        if not pos:
            start = "1.0" if forward else tk.END
            pos = widget.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop, nocase=True)

        if pos:
            widget.tag_remove(tk.SEL, "1.0", tk.END)
            end_pos = f"{pos}+{len(text)}c"
            widget.tag_add(tk.SEL, pos, end_pos)
            widget.mark_set(tk.INSERT, end_pos)
            widget.mark_set("tk::anchor1", pos)
            widget.see(tk.INSERT)
    return "break"


def search_lines(widget, search_text):
    matching_lines = []
    start_index = "1.0"
    while True:
        start_index = widget.search(search_text, start_index, stopindex=tk.END, nocase=True)
        if not start_index: break
        matching_lines.append((start_index,widget.get(f"{start_index} linestart", f"{start_index} lineend")))
        start_index = f"{start_index}+{len(search_text)}c"

    return matching_lines


def find_all(text):
    log_path = "/".join((_sess_dir,"find_all.log"))
    with open(log_path, "w") as log_file:
        msg = f"find all results matching: {text}\nin {len(files)} files"
        print(msg, file=log_file)
        print("".ljust(len(msg), "-"), file=log_file)
        start = time.time()
        for k, v in zip(shorten_paths([f["path"] for f in files.values()]), files.values()):
            for l in search_lines(v["editor"], text):
                line,row,out = *l[0].split("."), l[1]
                print(f"file://{k}:{line}:{row}: {out}", file=log_file)
        print(f"\ndone. {time.time()-start:.2f} secs", file=log_file)
        
    file_open(log_path)


def update_tags(text: EventText, start="1.0", end=tk.END):
    if text.tag_regex:
        for tag in text.tag_names():
            if tag in [tk.SEL]: continue
            text.tag_remove(tag, start, end)

        for match in text.tag_regex.finditer(text.get(start, end)):
            groups = {k:v for k,v in match.groupdict().items() if v}
            for k in groups:
                sp_start, sp_end = match.span(k)
                sp_start = f"{start} + {sp_start}c"
                sp_end = f"{start} + {sp_end}c"
                text.tag_add(k, sp_start, sp_end)


def editor_modified(widget):
    if widget.read_only: return
    widget.edits = True
    update_title(widget)
    args = widget.event_args
    start = end = widget.index(tk.INSERT)
    line, _ = map(int, start.split("."))
    lines = 16
    if args and len(args) > 1:
        lines = len(args[-1].split("\n"))
        start = f"{line-lines}.{0}"
        start += f" - {len(args[-1])}c"
        start = widget.index(start)
        start = f"{start.split('.')[0]}.0"
        end = f"{line+lines}.{0}"
    else:
        start = f"{line-lines}.{0}"
        end = f"{line+lines}.{0}"

    if lines < 64: update_tags(widget, start, end)
    if widget.tag_line > line-lines: widget.tag_line = 1



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
    complist_update_start(palette.get())
    text = palette.get()
    index = text.find(":")
    if index != -1: palette.selection_range(index+2, tk.END)
    else: palette.selection_range(0, tk.END)
    return "break"

# -----------------------------------------------------

def complist_update_start(text, force = False):
    global last_complist
    if not root.focus_get(): return
    if root.focus_get() == editor: return
    if text != last_complist or force:
        match_func = None
        last_complist = text
        complist.delete(0, tk.END)
        complist.place_forget()
        if ": " in text:
            cmd, text = text.split(": ", maxsplit=1)
            if cmd in commands and "match_cb" in commands[cmd]:
                match_func = commands[cmd]["match_cb"]
        else:
            match_func = lambda x: [k+": " for k in commands if x in k]

        if match_func:
            def match_thread(match_func, text): complist_update_end(text, match_func(text))
            threading.Thread(target=match_thread, args=(match_func, text), name="matching").start()


def complist_update_end(text, matches):
    match_lock.acquire()
    if last_complist.endswith(text):
        complist.delete(0, tk.END)
        complist.place_forget()
        for match in matches: complist.insert(tk.END, match)
        size = complist.size()
        if size:
            width = len(max(matches, key=len))+1 if matches else 0
            complist.configure(width=width, height=size)
            complist.place(x=palette.winfo_x(), y=palette.winfo_y(), anchor="sw")
    match_lock.release()


def complist_configure():
    if not root.focus_get(): return
    if editor == root.focus_get(): return
    complist.place(x=palette.winfo_x(), y=palette.winfo_y(), anchor="sw")
    if complist.winfo_height() > editor.winfo_height():
        complist.place_configure(height=editor.winfo_height())


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
        complist_update_start(cmd+selected_text)
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
    return sorted(filter(file_filter, ret), key=lambda x: x.lower().index(basename))


def cmd_glob_matches(text):
    ret = []
    if text not in glob_map:
        ret = glob.glob(text, recursive=True)
        glob_map[text] = ret

    else: ret = glob_map[text]

    if not ret or (len(ret) == 1 and ret[0] == text): ret = cmd_open_matches(text)
    return ret


def cmd_tab_matches(text):
    low_text = text.lower()
    dirname, basename = os.path.split(low_text)
    def file_filter(word):
        if len(low_text) >= len(word): return False
        low_word = word.lower()
        base_word = low_word.replace(dirname, "")
        return (basename in base_word) or (fnmatch.fnmatch(low_word, low_text))
    paths = [files[p]["path"] for p in files.keys()]
    if paths: return sorted(filter(file_filter, shorten_paths(paths)), key=lambda x: x.lower().index(basename) if basename in x else 999)
    return []


def cmd_cache_matches(text):
    low_text = text.lower()
    def file_filter(word): return (low_text in word.lower())
    paths = [f.replace(".pkl", "") for f in os.listdir(_grampy_dir) if f.endswith(".pkl")]
    if paths: return sorted(filter(file_filter, paths), key=lambda x: x.lower().index(low_text))
    return []


def cmd_exec(text):
    try: exec(text, globals(), locals())
    except Exception as e: print(e)


def cmd_open(text, new_instance=False):
    if "*" in text:
        complist.place_forget()
        args = complist.get(0, tk.END)
        msg = f"opening {len(args)} files matching: {text}"
        print("".ljust(len(msg), "-"))
        print(msg)
        print("".ljust(len(msg), "-"), flush=True)
        show_stdout()
        root.update()
        def open_all(files):
            start = time.time()
            share_work(lambda x: list(map(lambda y: file_open(y, background=True), x)), files)
            print(f"\ndone. {time.time()-start:.2f} secs")
            print("".ljust(32, "-"))
        
        if args:
            if len(args) > 1: threading.Thread(target=open_all, args=([args]), name="open_all").start()
            else: file_open(args[0], new_instance)
    else:
        file_open(text, new_instance)


def cmd_tab(text, new_instance=False):
    paths = [files[p]["path"] for p in files.keys()]
    paths = zip(paths, shorten_paths(paths))
    path = next((x for x, y in paths if y.endswith(text)), "")
    if path: file_open(path, new_instance)
    palette.delete(len("tab: "), tk.END)


def cmd_cache(text, new_instance=False):
    global cache_name
    cache_name = text
    print("Setting cache to "+cache_name)
    show_stdout()
    if os.path.exists("/".join((_grampy_dir, text+".pkl"))):
        pkl_files = pickle.load(open("/".join((_grampy_dir, text+".pkl")), "rb"))
        print(f"Loading {len(pkl_files)} files from '{cache_name}' cache")
        def file_cache(in_files):
            start = time.time()            
            in_files = list(in_files.items())
            def cache_open(files):
                for k,v in files: file_get(k, cache=v)
            share_work(cache_open, in_files)
            print(f"done. {time.time()-start:.2f} secs")
        threading.Thread(target=file_cache, args=([pkl_files]), name="load_cache").start()


def cmd_register(name, command, match_cb=None, shortcut=None):
    global commands
    assert not name in commands, f"'{name}' already registered "
    cmd = {"command": command}
    if match_cb: cmd.update({"match_cb": match_cb})
    if shortcut:
        cmd.update({"shortcut": shortcut })
        root.bind(shortcut, lambda x: palette_op(name))
    commands[name] = cmd

# -----------------------------------------------------

def fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes("-fullscreen", is_fullscreen)


if os.name == "nt":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(2)

args = sys.argv[1:]
root = tk.Tk()

for arg in args:
    if arg.startswith("geo="):
        x,y,width,height = ast.literal_eval(arg.replace("geo=", ""))
        root.geometry('%dx%d+%d+%d' % (width, height, x, y))
        break
    

if os.name == "nt": root.title("")
else: root.title("grampy")

photo = tk.PhotoImage(data=_grampy_icon)
root.wm_iconphoto(False, photo)
root.configure(background=config["text"]["background"])

root.bind("<Control-s>", lambda _: save_file(current_file))
root.bind("<Control-m>", lambda _: file_open(conf_path))
root.bind("<Control-p>", lambda _: show_stdout())

cmd_register("open", lambda x: cmd_open(*x) , cmd_glob_matches, "<Control-o>")
cmd_register("tab", lambda x: cmd_tab(*x), cmd_tab_matches, "<Control-t>")
cmd_register("cache", lambda x: cmd_cache(*x), cmd_cache_matches, "<Control-i>")

cmd_register("find", lambda x: find_text(editor, *x), shortcut="<Control-f>")
cmd_register("find all", lambda x: find_all(x[0]), shortcut="<Control-F>")
cmd_register("exec", lambda x: cmd_exec(x[0]), shortcut="<Control-e>")
cmd_register("save as", lambda x: (save_file(x[0]), file_open(x[0])), cmd_open_matches, "<Control-S>")

editor = EventText(root, wrap='none', undo=True)
complist = tk.Listbox(root, relief='flat')

complist.bind("<Configure>", lambda _: complist_configure())
complist.bind("<Double-Button-1>", complist_insert)
complist.bind("<Return>", complist_insert)
complist.bind("<Tab>", complist_insert)
complist.bind("<Escape>", lambda x: palette.focus_set())
complist.bind("<Down>", lambda _: "")
complist.bind("<Up>", lambda _: "")
complist.bind("<Shift_L>", lambda _: "")
complist.bind("<Shift_R>", lambda _: "")
complist.bind("<Key>", lambda x: (palette.insert(tk.END, x.char), palette.focus_set()))
complist.configure(borderwidth=0, selectborderwidth=0)
complist.configure(activestyle='none')

palette = tk.Entry(root)
palette_cus = lambda x=None: complist_update_start(palette.get())
palette.bind("<Control-a>", palette_select_all)
palette.bind("<Configure>", lambda _: complist_configure())
palette.bind("<Control-w>", lambda x: file_close(editor.path))
palette.bind("<KeyRelease>", lambda x: palette_cus() if 31<x.keysym_num<200 else "")
palette.bind("<KeyRelease-BackSpace>", palette_cus)
palette.bind("<KeyRelease-Delete>", palette_cus)
palette.bind('<FocusIn>', lambda x: palette.focus_set())
palette.bind("<Control-BackSpace>", lambda x: (delete_to_break(palette), palette_cus()))
palette.bind("<Control-Delete>", lambda x: (delete_to_break(palette, False), palette_cus()))
palette.bind("<Escape>", lambda x: editor.focus_set())
palette.bind("<Tab>", lambda x: complist_insert(None, 0))
palette.bind("<Down>", lambda x: (complist.focus_set(), complist.select_set(0)) if complist.size() else "")
palette.configure(borderwidth=0)
palette.pack(fill="x")
apply_config(editor)
os.chdir(os.path.expanduser("~"))
if args and os.path.exists(args[0]): file_open(args[0])
else:
    readme = os.path.join(os.path.dirname(__file__),"README.md")
    if os.path.exists(readme): file_open(readme, read_only=True)
    else:
        new_file = "new_file.txt"
        for i in range(0, 1000):
            if not os.path.exists(new_file): break
            new_file = f"new_file{i}.txt"
        file_open(new_file)


def watch_file():
    global conf_mtime
    do_update = False
    update_time = 100
    try:
        sys.stdout.flush()
        if destroy_list: dest = destroy_list.pop(); dest.destroy()
        if editor.edits and not editor.edit_modified(): editor.edits = False; update_title(editor)
        if os.path.isfile(editor.path):
            mtime = os.path.getmtime(editor.path)
            if mtime != editor.mtime:
                if not editor.edits:
                    editor.mtime = mtime
                    ins = editor.index(tk.INSERT); end = editor.index(tk.END+" - 1c")
                    if editor.read_only: editor.configure(state=tk.NORMAL)
                    editor.delete("1.0", tk.END)
                    editor.insert(tk.END, open(editor.path).read())
                    if editor.compare(ins, ">=", end): editor.mark_set(tk.INSERT, tk.END)
                    else: editor.mark_set(tk.INSERT, ins)
                    if editor.read_only: editor.configure(state=tk.DISABLED)
                    editor.see(tk.INSERT)
                    editor.edits = False
                    editor.extern_edits = False
                    do_update = True
                    update_title(editor)
                elif not editor.extern_edits:
                    editor.extern_edits = True
                    root.bell()
                    update_title(editor)
        mtime = os.path.getmtime(conf_path)

        if mtime != conf_mtime:
            conf_mtime = mtime
            apply_config(editor)
            do_update = True
        if do_update: editor.tag_line = 1
        if step_tags(): update_time = 10
    except Exception as e:
        print(e, file=sys.stderr)
    root.after(update_time, watch_file)

watch_file()
root.mainloop()

sys.stdout = sys.__stdout__
for file in os.listdir(_sess_dir):
    key = file_to_key("/".join((_sess_dir, file)))
    if key in files: files.pop(key)
time.sleep(.1)
shutil.rmtree(_sess_dir, ignore_errors=True)
if cache_name:
    files = {k: v["editor"].get("1.0", tk.END) for k,v in files.items()}
    pickle.dump(files, open("/".join((_grampy_dir, cache_name+".pkl")), "wb"))
