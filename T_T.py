import re
import tkinter as tk
import idlelib.colorizer as ic
import idlelib.percolator as ip
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



cdg = ic.ColorDelegator()
cdg.prog = re.compile(Py.PROG, re.S)
cdg.idprog = re.compile(r'\s+(\w+)', re.S)

cdg.tagdefs['MYGROUP'] = {'foreground': '#7F7F7F', 'background': TextCol.bg}
cdg.tagdefs[tk.SEL] = {'foreground': TextCol.fg, 'background': TextCol.selected}
cdg.tagdefs[tk.INSERT] = {'foreground': TextCol.fg, 'background': TextCol.selected}
# These five lines are optional. If omitted, default colours are used.
cdg.tagdefs['COMMENT'] = {'foreground': TextCol.comment, 'background': TextCol.bg}
cdg.tagdefs['KEYWORD'] = {'foreground': TextCol.keyword, 'background': TextCol.bg}
cdg.tagdefs['BUILTIN'] = {'foreground': TextCol.builtin, 'background': TextCol.bg}
cdg.tagdefs['STRING'] = {'foreground': TextCol.string, 'background': TextCol.bg}
cdg.tagdefs['DEFINITION'] = {'foreground': TextCol.definition, 'background': TextCol.bg}

current_file_path = None
root = tk.Tk()

def save_file(event=None):
    global current_file_path
    if not current_file_path:
        current_file_path = asksaveasfilename(defaultextension=".txt")
        if not current_file_path:
            return
    with open(current_file_path, "w") as output_file:
        text = text_box.get(1.0, tk.END)
        output_file.write(text)


def open_file(event=None):
    global root
    global current_file_path
    file_path = askopenfilename()
    if not file_path:
        return
    current_file_path = file_path
    text_box.delete(1.0, tk.END)
    with open(current_file_path, "r") as input_file:
        text = input_file.read()
        text_box.insert(tk.END, text)
    root.title(current_file_path)


def select_all_editor(event=None):
    text_box.tag_add(tk.SEL, "1.0", tk.END)
    text_box.mark_set(tk.INSERT, "1.0")
    text_box.see(tk.INSERT)
    return 'break'


def editor_find(event=None):
    palette.focus_set()
    def find_text(forward = True):
        text = palette.get()
        if text:
            start = text_box.index("insert")
            stop = (tk.END if forward else "1.0")
            if not forward: start += f"- {len(text)}c"
            pos = text_box.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop)
            if not pos:
                start = "1.0" if forward else tk.END
                pos = text_box.search(text, start, forwards=forward, backwards=(not forward), stopindex=stop)
            
            if pos:
                text_box.tag_remove(tk.SEL, "1.0", tk.END)
                end_pos = f"{pos}+{len(text)}c"

                text_box.tag_add(tk.SEL, pos, end_pos)
                text_box.mark_set(tk.INSERT, end_pos)
                text_box.see(tk.INSERT)
        
    palette.bind("<Return>", lambda event: find_text())
    palette.bind("<Shift-Return>", lambda event: find_text(False))

root.title("T_T")
root.bind("<Control-f>", editor_find)
root.bind("<Control-s>", save_file)
root.bind("<Control-o>", open_file)
root.bind("<Control-w>", lambda x: root.quit())
root.bind("<Escape>", lambda x: text_box.focus_set())

text_box = tk.Text(root, insertbackground=TextCol.fg, wrap='none', height=30, width=60, undo=True, font=('Courier', 15), foreground=TextCol.fg, background=TextCol.bg)

text_box.bind("<Control-a>", select_all_editor)
text_box.bind("<Control-f>", editor_find)
text_box.pack(expand=True, fill="both")

palette = tk.Entry(root, width=60)
palette.bind("<Control-a>", lambda x: palette.selection_range(0, tk.END))
palette.bind('<FocusIn>', lambda x: palette.selection_range(0, tk.END))
palette.pack(fill="x")


ip.Percolator(text_box).insertfilter(cdg)

root.mainloop()
