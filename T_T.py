import re
import tkinter as tk
import idlelib.colorizer as ic
import idlelib.percolator as ip
from tkinter.filedialog import asksaveasfilename, askopenfilename

cdg = ic.ColorDelegator()
cdg.prog = re.compile(r'\b(?P<MYGROUP>tkinter)\b|' + ic.make_pat().pattern, re.S)
cdg.idprog = re.compile(r'\s+(\w+)', re.S)

cdg.tagdefs['MYGROUP'] = {'foreground': '#7F7F7F', 'background': '#FFFFFF'}

# These five lines are optional. If omitted, default colours are used.
cdg.tagdefs['COMMENT'] = {'foreground': '#FF0000', 'background': '#FFFFFF'}
cdg.tagdefs['KEYWORD'] = {'foreground': '#007F00', 'background': '#FFFFFF'}
cdg.tagdefs['BUILTIN'] = {'foreground': '#7F7F00', 'background': '#FFFFFF'}
cdg.tagdefs['STRING'] = {'foreground': '#7F3F00', 'background': '#FFFFFF'}
cdg.tagdefs['DEFINITION'] = {'foreground': '#007F7F', 'background': '#FFFFFF'}

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

text_box = tk.Text(root, height=30, width=60, undo=True)

text_box.bind("<Control-a>", select_all_editor)
text_box.bind("<Control-f>", editor_find)
text_box.pack(expand=True, fill="both")

palette = tk.Entry(root, width=60)
palette.bind("<Control-a>", lambda x: palette.selection_range(0, tk.END))
palette.bind('<FocusIn>', lambda x: palette.selection_range(0, tk.END))
palette.pack(fill="x")


ip.Percolator(text_box).insertfilter(cdg)

root.mainloop()
