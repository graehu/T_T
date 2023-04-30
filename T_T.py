import re
import tkinter as tk
from tkinter.filedialog import asksaveasfilename, askopenfilename


colors = { "BLACK": "#000000", "WHITE": "#FFFFFF", "RED": "#FF0000",
          "GREEN": "#00FF00", "BLUE": "#0000FF", "YELLOW": "#FFFF00",
          "MAGENTA": "#FF00FF", "CYAN": "#00FFFF", "GRAY": "#808080", 
          "DARK_GRAY": "#404040", "DARKER_GRAY": "#252525",
          "LIGHT_GRAY": "#C0C0C0", "ORANGE": "#FFA500",
          "PURPLE": "#800080", "BROWN": "#A52A2A", "PINK": "#FFC0CB",
          "LIGHT_PINK": "#FFB6C1", "GOLD": "#FFD700", "NAVY": "#000080",
          "TEAL": "#008080", "DARK_RED": "#B80000", "DARK_GREEN":"#009000", "DARKER_GREEN":"#008000",
          "DARK_BLUE": "#000080", "DARK_YELLOW": "#B8B800",
          "DARK_MAGENTA": "#800080", "DARK_CYAN": "#008080", "LIGHT_RED": "#FF8080",
          "LIGHT_GREEN": "#80FF80", "LIGHT_BLUE": "#8080FF", "LIGHT_YELLOW": "#FFFF80",
          "LIGHT_MAGENTA": "#FF80FF", "LIGHT_CYAN": "#80FFFF"
}


class TextCol:
    fg = colors["LIGHT_GRAY"]
    bg =  colors["DARKER_GRAY"]
    selected = colors["DARK_GRAY"]
    comment = colors["DARKER_GREEN"]
    keyword = colors["LIGHT_MAGENTA"]
    builtin = colors["GOLD"]
    string = colors["DARK_GREEN"]
    definition = colors["LIGHT_BLUE"]


class Py:
    KEYWORD   = r"\b(?P<KEYWORD>False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
    EXCEPTION = r"([^.'\"\\#]\b|^)(?P<EXCEPTION>ArithmeticError|AssertionError|AttributeError|BaseException|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EnvironmentError|Exception|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError)\b"
    BUILTIN   = r"([^.'\"\\#]\b|^)(?P<BUILTIN>abs|all|any|ascii|bin|breakpoint|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dir|divmod|enumerate|eval|exec|exit|filter|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|isinstance|issubclass|iter|len|license|locals|map|max|memoryview|min|next|oct|open|ord|pow|print|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|sum|type|vars|zip)\b"
    DOCSTRING = r"(?P<DOCSTRING>(?i:r|u|f|fr|rf|b|br|rb)?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?|(?i:r|u|f|fr|rf|b|br|rb)?\"\"\"[^\"\\]*((\\.|\"(?!\"\"))[^\"\\]*)*(\"\"\")?)"
    STRING    = r"(?P<STRING>(?i:r|u|f|fr|rf|b|br|rb)?'[^'\\\n]*(\\.[^'\\\n]*)*'?|(?i:r|u|f|fr|rf|b|br|rb)?\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
    TYPES     = r"\b(?P<TYPES>bool|bytearray|bytes|dict|float|int|list|str|tuple|object)\b"
    NUMBER    = r"\b(?P<NUMBER>((0x|0b|0o|#)[\da-fA-F]+)|((\d*\.)?\d+))\b"
    CLASSDEF  = r"(?<=\bclass)[ \t]+(?P<CLASSDEF>\w+)[ \t]*[:\(]" #recolor of DEFINITION for class definitions
    DECORATOR = r"(^[ \t]*(?P<DECORATOR>@[\w\d\.]+))"
    INSTANCE  = r"\b(?P<INSTANCE>super|self|cls)\b"
    COMMENT   = r"(?P<COMMENT>#[^\n]*)"
    SYNC      = r"(?P<SYNC>\n)"
    PROG      = rf"{KEYWORD}|{BUILTIN}|{EXCEPTION}|{TYPES}|{COMMENT}|{DOCSTRING}|{STRING}|{SYNC}|{INSTANCE}|{DECORATOR}|{NUMBER}|{CLASSDEF}"


class Tagger:
    regex: re = None
    tags = {}
    
    def __init__(self, tags, regex):
        self.regex = re.compile(regex, re.S)
        self.tags = tags

    def update(self, text: tk.Text, start="1.0", end=tk.END):
        
        for tag in text.tag_names():
            if tag in [tk.SEL]: continue
            text.tag_remove(tag, start, end)
        
        for match in self.regex.finditer(text.get(start, end)):
            groups = {k:v for k,v in match.groupdict().items() if v}
            for k in groups:
                sp_start, sp_end = match.span(k)
                sp_start = f"{start} + {sp_start}c"
                sp_end = f"{start} + {sp_end}c"
                text.tag_add(k, sp_start, sp_end)


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
        result = self.tk.call(cmd)
        if command in ("insert", "delete", "replace"):
            self.event_args = args
            self.event_generate("<<TextModified>>")
        
        if command in ("yview", "xview"):
            self.event_generate("<<ViewUpdated>>")

        return result


tags = {}
tags[tk.SEL] = {'foreground': TextCol.fg, 'background': TextCol.selected}
tags['COMMENT'] = {'foreground': TextCol.comment, 'background': TextCol.bg}
tags['CLASSDEF'] = {'foreground': TextCol.string, 'background': TextCol.bg}
tags['KEYWORD'] = {'foreground': TextCol.keyword, 'background': TextCol.bg}
tags['BUILTIN'] = {'foreground': TextCol.builtin, 'background': TextCol.bg}
tags['STRING'] = {'foreground': TextCol.string, 'background': TextCol.bg}
tags['DEFINITION'] = {'foreground': TextCol.definition, 'background': TextCol.bg}

for k in tags:
    tags[k].update({"selectforeground": tags[k]["foreground"]})
    tags[k].update({"selectbackground": tags[tk.SEL]["background"]})

current_file_path = None
root = tk.Tk()

def save_file(event=None):
    global current_file_path
    if not current_file_path:
        current_file_path = asksaveasfilename(defaultextension=".txt")
        if not current_file_path:
            return
    
    with open(current_file_path, "w") as output_file:
        text = editor.get(1.0, tk.END)
        output_file.write(text)


def open_file(event=None):
    global root
    global current_file_path
    file_path = askopenfilename()
    if not file_path:
        return
    
    current_file_path = file_path
    editor.delete(1.0, tk.END)
    with open(current_file_path, "r") as input_file:
        text = input_file.read()
        editor.insert(tk.END, text)
    root.title(current_file_path)


def editor_select_all(event=None):
    editor.tag_add(tk.SEL, "1.0", tk.END)
    editor.mark_set(tk.INSERT, "1.0")
    editor.see(tk.INSERT)
    return 'break'


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
            editor.see(tk.INSERT)
    return 'break'


def editor_modified(event=None):
    args = editor.event_args
    
    start = end = editor.index(tk.INSERT)
    line, char = map(int, start.split("."))
    if len(args) > 1:
        start = f"{line-1}.{0}"
        start += f" - {len(args[-1])}c"
        start = editor.index(start)
        start = f"{start.split('.')[0]}.0"
        end = f"{line+1}.{0}"
    else:
        start = f"{line-1}.{0}"
        end = f"{line+1}.{0}"
    # end += f" + {len(args[-1])}c"
    # print((start, end))
    # start = editor.index("@0,0")
    # end = editor.index(f"@{editor.winfo_width()},{editor.winfo_width()}")
    tagger.update(editor, start, end)


def editor_find(event=None):
    palette.focus_set()    
    palette.bind("<Return>", lambda event: editor_find_text(palette.get()))
    palette.bind("<Shift-Return>", lambda event: editor_find_text(palette.get(), False))


def delete_word_backwords(widget):
    cursor = widget.index(tk.INSERT)
    start = cursor
    if not isinstance(cursor, int):
        while start != "1.0":
            wordstart = widget.index(f"{start} wordstart")
            if wordstart == start:
                start = widget.index(start +" - 1c")
            elif cursor.split('.')[0] != wordstart.split('.')[0]:
                start = f"{cursor.split('.')[0]}.0 - 1c"
                break
            else:
                start = f"{wordstart} + 1c"
                break
    else:
         text = widget.get()
         while start != 0:
            start -= 1
            if text[start] == " ":
                start +=1
                break
    widget.delete(f"{start}", cursor)


root.title("T_T")
root.bind("<Control-f>", editor_find)
root.bind("<Control-s>", save_file)
root.bind("<Control-o>", open_file)
root.bind("<Control-w>", lambda x: root.quit())
root.bind("<Escape>", lambda x: editor.focus_set())

editor = EventText(root, borderwidth=0, highlightthickness=0, insertbackground=TextCol.fg, wrap='none', height=30, width=60, undo=True, font=('Courier', 15), foreground=TextCol.fg, background=TextCol.bg)
tagger = Tagger(tags, Py.PROG)
editor.bind("<<TextModified>>", editor_modified)
editor.bind("<Control-a>", editor_select_all)
editor.bind("<Control-f>", editor_find)
editor.bind("<Control-BackSpace>", lambda x: delete_word_backwords(editor))

for k in tags:
    editor.tag_configure(k, tags[k])

editor.pack(expand=True, fill="both")

separator = tk.Frame(root, bg=colors["DARK_GRAY"], height=1, bd=0)
separator.pack(fill="x")
palette = tk.Entry(root, width=60, relief='flat', insertbackground=TextCol.fg, foreground=TextCol.fg, background=TextCol.bg, font=('Courier', 15), highlightthickness=0)
palette.bind("<Control-a>", lambda x: palette.selection_range(0, tk.END))
palette.bind('<FocusIn>', lambda x: palette.selection_range(0, tk.END))
palette.bind("<Control-BackSpace>", lambda x: delete_word_backwords(palette))

palette.pack(fill="x")

root.mainloop()
