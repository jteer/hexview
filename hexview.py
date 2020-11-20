import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog

try:
    Spinbox = ttk.Spinbox
except AttributeError:
    Spinbox = tk.Spinbox

APPNAME = "Hex Viewer"
BLOCK_WIDTH = 16
BLOCK_HEIGHT = 32
BLOCK_SIZE = BLOCK_WIDTH * BLOCK_HEIGHT
ENCODINGS = ("ASCII", "CP037", "CP850", "CP1140", "CP1252",
             "Latin1", "ISO8859_15", "Mac_Roman", "UTF-8",
             "UTF-8-sig", "UTF-16", "UTF-32")

class MainWindow:

    def __init__(self, parent):
        self.parent = parent
        self.initialize_variables()
        self.setup_widgets()
        self.setup_layout()
        self.setup_key_bindings()
        # if opening app from command line with file path arg
        if len(sys.argv) > 1:
            self._open(sys.argv[1])

    def initialize_variables(self):
        self.filename = None
        self.offset = tk.IntVar()
        self.offset.set(0)
        self.encoding = tk.StringVar()
        self.encoding.set(ENCODINGS[0])
    
    def setup_widgets(self):
        frame = self.frame = ttk.Frame(self.parent)
        self.openButton = ttk.Button(frame, text="Open File", underline=0, command=self.open)
        self.offsetLabel = ttk.Label(frame, text="Offset", underline=1)
        self.offsetSpinbox = Spinbox(frame, from_=0, textvariable=self.offset, increment=BLOCK_SIZE)
        self.encodingLabel = ttk.Label(frame, text="Encoding", underline=0)
        self.encodingCombobox = ttk.Combobox(frame, values=ENCODINGS, textvariable=self.encoding,
                                             state="readonly")
        self.create_view()
    
    def create_view(self):
        self.viewText = tk.Text(self.frame, height=BLOCK_HEIGHT, width=2 + (BLOCK_WIDTH * 4))
        self.viewText.tag_configure("ascii", foreground="green")
        self.viewText.tag_configure("error", foreground="red")
        self.viewText.tag_configure("hexspace", foreground="navy")
        self.viewText.tag_configure("graybg", background="lightgray")
        self.viewText.tag_configure("even", background="#e0e0e0")
        self.viewText.tag_configure("odd", background="#ffffff")
        self.viewText.tag_raise(tk.SEL)

 
    def setup_layout(self):
        grid_row_buttons = [self.openButton, self.offsetLabel, self.offsetSpinbox,
                            self.encodingLabel, self.encodingCombobox]
        for column, widget in enumerate(grid_row_buttons):
            widget.grid(row=0, column=column, sticky=tk.W)
        self.viewText.grid(row=1, column=0, columnspan=6, sticky=tk.NSEW)
        self.frame.grid(row=0, column=0, sticky=tk.NSEW)
    
    def setup_key_bindings(self):
        for keypress in ("<Control-o>", "<Alt-o>"):
            self.parent.bind(keypress, self.open)
        for keypress in ("<Control-q>", "<Alt-q>", "<Escape>"):
            self.parent.bind(keypress, self.quit)
        self.parent.bind("<Alt-f>",
                         lambda *args: self.offsetSpinbox.focus())
        self.parent.bind("<Alt-e>",
                         lambda *args: self.encodingCombobox.focus())
        for variable in (self.offset, self.encoding):
            variable.trace_variable("w", self.show_block)
    
    def show_block(self, *args):
        self.viewText.delete("1.0", tk.END)
        if not self.filename:
            return
        with open(self.filename, "rb") as file:
            try:
                file.seek(self.offset.get(), os.SEEK_SET)
                block = file.read(BLOCK_SIZE)
            except ValueError:
                return
        
        rows = [block[i:i + BLOCK_WIDTH] for i in range(0, len(block), BLOCK_WIDTH)]
        
        for row in rows:
            self.show_bytes(row)
            self.show_text(row)
        
        self.viewText.insert(tk.END, "\n")
        self.highlight()

    def highlight(self):
        lastline = self.viewText.index("end-1c").split(".")[0]
        tag = "odd"
        for i in range(1, int(lastline)):
            self.viewText.tag_add(tag, "%s.0" % i, "%s.0" % (i+1))
            tag = "even" if tag == "odd" else "odd"

    def show_bytes(self, row):
        for byte in row:
            tags = ()
            if byte in b"\t\n\r\v\f":
                tags = ("hexspace", "graybg")
            elif 0x20 < byte < 0x7F:
                tags = ("ascii",)
            self.viewText.insert(tk.END, f"{byte:02X}", tags)
            self.viewText.insert(tk.END, " ")
        if len(row) < BLOCK_WIDTH:
            self.viewText.insert(tk.END, " " * (BLOCK_WIDTH - len(row)) * 3)

    def show_text(self, row):
        for char in row.decode(self.encoding.get(), errors="replace"):
            tags = ()
            if char in "\u2028\u2029\t\n\r\v\f\uFFFD":
                char = "."
                tags = ("graybg" if char == "\uFFFD" else "error",)
            elif 0x20 < ord(char) < 0x7F:
                tags = ("ascii",)
            elif not 0x20 <= ord(char) <= 0xFFFF: # Tcl/Tk limit
                char = "?"
                tags = ("error",)
            self.viewText.insert(tk.END, char, tags)
        self.viewText.insert(tk.END, "\n")

    def open(self, *args):
        self.viewText.delete("1.0", tk.END)
        self.offset.set(0)
        filename = filedialog.askopenfilename(title=f"{APPNAME} - Find a file")
        self._open(filename)

    def _open(self, filename):
        if filename and os.path.exists(filename):
            self.parent.title(f"{APPNAME} — {filename}")
            size = os.path.getsize(filename)
            size = (size - BLOCK_SIZE if size > BLOCK_SIZE else
                    size - BLOCK_WIDTH)
            self.offsetSpinbox.config(to=max(size, 0))
            self.filename = filename
            self.show_block()
    
    def quit(self, event=None):
        self.parent.destroy()
        
app = tk.Tk()
app.title(APPNAME)
window = MainWindow(app)
app.protocol("WM_DELETE_WINDOW", window.quit)
app.resizable(width=False, height=False)
app.mainloop()