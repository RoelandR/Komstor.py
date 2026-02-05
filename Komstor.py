import tkinter as tk
from tkinter import ttk
import sqlite3
import webbrowser
import os
import shutil
from datetime import datetime
import sys

DB_NAME = "comstor.db"

# ---------------------------------------------------------
# Altijd werken vanuit de map van dit script
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
db_path = os.path.join(script_dir, DB_NAME)


class ComStorApp:
    def __init__(self, root):
        self.root = root

        # Uniform font overal
        self.fixed_font = ("Courier New", 14)

        # Windows: custom titelbalk
        # Linux/macOS: normale titelbalk (focus werkt dan altijd)
        if sys.platform.startswith("win"):
            self.root.overrideredirect(True)
            self.build_titlebar()
        else:
            self.root.title("ComStor")

        first_time = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path)

        if first_time:
            self.create_empty_database_with_locations()
        else:
            self.ensure_table_exists()
            self.ensure_locations_exist()

        self.build_ui()
        self.load_records()
        self.update_title_with_backup_info()

    # ---------------------------------------------------------
    # Custom titelbalk (alleen Windows)
    # ---------------------------------------------------------
    def build_titlebar(self):
        self.titlebar = tk.Frame(self.root, bg="blue", relief="flat", bd=0)
        self.titlebar.pack(fill="x")

        self.title_label = tk.Label(
            self.titlebar,
            text="ComStor",
            bg="blue",
            fg="yellow",
            font=("Courier New", 18, "bold")
        )
        self.title_label.pack(side="left", padx=10)

        close_btn = tk.Button(
            self.titlebar,
            text=" X ",
            bg="#cc0000",
            fg="yellow",
            font=("Courier New", 16, "bold"),
            bd=0,
            command=self.root.destroy
        )
        close_btn.pack(side="right")

        # Venster verslepen
        def start_move(event):
            self.x = event.x
            self.y = event.y

        def stop_move(event):
            self.x = None
            self.y = None

        def do_move(event):
            if self.x is None or self.y is None:
                return
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        self.titlebar.bind("<ButtonPress-1>", start_move)
        self.titlebar.bind("<ButtonRelease-1>", stop_move)
        self.titlebar.bind("<B1-Motion>", do_move)

    # ---------------------------------------------------------
    # Backup info ophalen + titel / titelbalk bijwerken
    # ---------------------------------------------------------
    def get_last_backup_info(self):
        backup_dir = os.path.join(script_dir, "backup")
        if not os.path.exists(backup_dir):
            return None

        backups = [
            f for f in os.listdir(backup_dir)
            if f.startswith("backup_") and f.endswith(".db")
        ]
        if not backups:
            return None

        backups.sort()
        last = backups[-1]
        full_path = os.path.join(backup_dir, last)

        timestamp = os.path.getmtime(full_path)
        dt = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        return last, dt

    def update_title_with_backup_info(self):
        info = self.get_last_backup_info()
        if info:
            name, dt = info
            if sys.platform.startswith("win"):
                self.title_label.config(text=f"ComStor — Laatste backup: {name} ({dt})")
            else:
                self.root.title(f"ComStor — Laatste backup: {name} ({dt})")
        else:
            if sys.platform.startswith("win"):
                self.title_label.config(text="ComStor — Geen backups gevonden")
            else:
                self.root.title("ComStor — Geen backups gevonden")

    # ---------------------------------------------------------
    # Database-initialisatie
    # ---------------------------------------------------------
    def ensure_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compnr TEXT,
                name TEXT,
                stock INTEGER,
                locatie TEXT,
                description TEXT,
                url TEXT
            )
        """)
        self.conn.commit()

    def ensure_locations_exist(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM components")
        if cur.fetchone()[0] == 0:
            self.create_empty_database_with_locations()

    def create_empty_database_with_locations(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compnr TEXT,
                name TEXT,
                stock INTEGER,
                locatie TEXT,
                description TEXT,
                url TEXT
            )
        """)

        LOK_LETTER = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P"]
        LOK_CIJFER = [
            '1A','2A','3A','4A','5A','6A','7A','8A',
            '1B','2B','3B','4B','5B','6B','7B','8B'
        ]

        for x in LOK_LETTER:
            for y in LOK_CIJFER:
                locatie = x + y
                cur.execute("INSERT INTO components (locatie) VALUES (?)", (locatie,))

        self.conn.commit()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Zoekveld
        search_frame = tk.Frame(main)
        search_frame.pack(fill="x", pady=(0, 10))

        tk.Label(search_frame, text="Zoek:", font=self.fixed_font).pack(side="left")
        self.search_var = tk.StringVar()
        entry = tk.Entry(search_frame, textvariable=self.search_var, font=self.fixed_font, width=20)
        entry.pack(side="left", padx=10)
        entry.bind("<KeyRelease>", lambda e: self.search())

        # Lijst links
        left = tk.Frame(main)
        left.pack(side="left", fill="y")

        self.tree = ttk.Treeview(
            left,
            columns=("locatie", "compnr", "name", "stock"),
            show="headings",
            height=20
        )

        self.tree.heading("locatie", text="Lokatie", command=lambda: self.sort_column("locatie", False))
        self.tree.heading("compnr", text="Compnr", command=lambda: self.sort_column("compnr", False))
        self.tree.heading("name", text="Naam", command=lambda: self.sort_column("name", False))
        self.tree.heading("stock", text="Voorraad", command=lambda: self.sort_column("stock", False))

        self.tree.pack(fill="y", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Detailvelden rechts
        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        # Lokatie read-only
        tk.Label(right, text="Lokatie:", font=self.fixed_font).grid(row=0, column=0, sticky="w")
        self.locatie_var = tk.StringVar()
        loc_entry = tk.Entry(right, textvariable=self.locatie_var, font=self.fixed_font, state="readonly")
        loc_entry.grid(row=0, column=1, sticky="ew")

        # Compnr
        tk.Label(right, text="Compnr:", font=self.fixed_font).grid(row=1, column=0, sticky="w")
        self.compnr_var = tk.StringVar()
        e = tk.Entry(right, textvariable=self.compnr_var, font=self.fixed_font)
        e.grid(row=1, column=1, sticky="ew")
        e.bind("<Return>", lambda e: self.save_record())
        e.bind("<KeyRelease>", self.mark_dirty)

        # Naam
        tk.Label(right, text="Naam:", font=self.fixed_font).grid(row=2, column=0, sticky="w")
        self.name_var = tk.StringVar()
        e = tk.Entry(right, textvariable=self.name_var, font=self.fixed_font)
        e.grid(row=2, column=1, sticky="ew")
        e.bind("<Return>", lambda e: self.save_record())
        e.bind("<KeyRelease>", self.mark_dirty)

        # Voorraad +/–
        tk.Label(right, text="Voorraad:", font=self.fixed_font).grid(row=3, column=0, sticky="w")
        stock_frame = tk.Frame(right)
        stock_frame.grid(row=3, column=1, sticky="ew")

        self.stock_var = tk.StringVar()

        # VALIDATOR: alleen cijfers
        vcmd = (self.root.register(self.validate_int), "%P")

        e = tk.Entry(
            stock_frame,
            textvariable=self.stock_var,
            font=self.fixed_font,
            width=10,
            validate="key",
            validatecommand=vcmd
        )
        e.pack(side="left")
        e.bind("<Return>", lambda e: self.save_record())
        e.bind("<KeyRelease>", self.mark_dirty)

        tk.Button(
            stock_frame, text="+", font=self.fixed_font, width=3,
            command=lambda: (self.increase_stock(), self.mark_dirty())
        ).pack(side="left", padx=5)
        tk.Button(
            stock_frame, text="-", font=self.fixed_font, width=3,
            command=lambda: (self.decrease_stock(), self.mark_dirty())
        ).pack(side="left")

        # Memo
        tk.Label(right, text="Omschrijving:", font=self.fixed_font).grid(row=4, column=0, sticky="w")
        self.memo = tk.Text(right, height=3, width=30, wrap="char", font=self.fixed_font, undo=True)
        self.memo.grid(row=4, column=1, sticky="ew")
        self.memo.bind("<Return>", lambda e: (self.save_record(), "break"))
        self.memo.bind("<KeyRelease>", self.mark_dirty)

        # URL
        tk.Label(right, text="URL:", font=self.fixed_font).grid(row=5, column=0, sticky="w")
        self.url_var = tk.StringVar()
        e = tk.Entry(right, textvariable=self.url_var, font=self.fixed_font)
        e.grid(row=5, column=1, sticky="ew")
        e.bind("<Return>", lambda e: self.save_record())
        e.bind("<KeyRelease>", self.mark_dirty)

        tk.Button(right, text="Open URL", command=self.open_url, font=self.fixed_font).grid(row=6, column=1, sticky="e")

        # Knoppenrij
        btn_frame = tk.Frame(right)
        btn_frame.grid(row=7, column=1, sticky="e", pady=10)

        # PRIMAIRE OPSLAAN-KNOP (start grijs)
        self.save_btn = tk.Button(
            btn_frame,
            text="OPSLAAN",
            command=self.save_record,
            font=("Courier New", 14, "bold"),
            bg="#cccccc",
            fg="#666666",
            activebackground="#cccccc",
            activeforeground="#666666",
            padx=10,
            pady=5,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=5)

        self.clear_btn = tk.Button(
            btn_frame, text="Wis record",
            font=self.fixed_font, state="disabled", command=self.clear_record
        )
        self.clear_btn.pack(side="left", padx=5)

        self.backup_btn = tk.Button(btn_frame, text="Backup", font=self.fixed_font, command=self.make_backup)
        self.backup_btn.pack(side="left", padx=5)

        # Grote afsluitknop rechtsonder
        self.big_close_btn = tk.Button(
            right,
            text="AFSLUITEN",
            font=("Courier New", 15, "bold"),
            bg="blue",
            fg="yellow",
            command=self.root.destroy
        )
        self.big_close_btn.grid(row=8, column=1, sticky="e", pady=20)

        right.columnconfigure(1, weight=1)

    # ---------------------------------------------------------
    # VALIDATOR: alleen cijfers
    # ---------------------------------------------------------
    def validate_int(self, new_value):
        if new_value == "":
            return True
        return new_value.isdigit()

    # ---------------------------------------------------------
    # Markeer dat er iets gewijzigd is
    # ---------------------------------------------------------
    def mark_dirty(self, event=None):
        self.save_btn.config(
            state="normal",
            bg="#0077cc",
            fg="white",
            activebackground="#005fa3",
            activeforeground="white"
        )

    # ---------------------------------------------------------
    # Kolommen sorteerbaar
    # ---------------------------------------------------------
    def sort_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        data.sort(reverse=reverse)

        for index, (val, k) in enumerate(data):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    # ---------------------------------------------------------
    # Voorraad + en -
    # ---------------------------------------------------------
    def increase_stock(self):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            value = int(self.stock_var.get() or "0")
        except ValueError:
            value = 0
        value += 1
        self.stock_var.set(str(value))
        self.update_clear_button()

    def decrease_stock(self):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            value = int(self.stock_var.get() or "0")
        except ValueError:
            value = 0
        if value > 0:
            value -= 1
        self.stock_var.set(str(value))
        self.update_clear_button()

    # ---------------------------------------------------------
    # Wis record (behalve lokatie)
    # ---------------------------------------------------------
    def clear_record(self):
        sel = self.tree.selection()
        if not sel:
            return

        rec_id = sel[0]

        cur = self.conn.cursor()
        cur.execute("""
            UPDATE components
            SET compnr=NULL, name=NULL, stock=NULL, description=NULL, url=NULL
            WHERE id=?
        """, (rec_id,))
        self.conn.commit()

        self.load_records()
        self.tree.selection_set(rec_id)
        self.update_clear_button()

    # ---------------------------------------------------------
    # Backup maken
    # ---------------------------------------------------------
    def make_backup(self):
        backup_dir = os.path.join(script_dir, "backup")
        os.makedirs(backup_dir, exist_ok=True)

        existing = [
            f for f in os.listdir(backup_dir)
            if f.startswith("backup_") and f.endswith(".db")
        ]

        numbers = []
        for f in existing:
            try:
                num = int(f.replace("backup_", "").replace(".db", ""))
                numbers.append(num)
            except ValueError:
                pass

        next_num = max(numbers) + 1 if numbers else 1
        filename = f"backup_{next_num:03d}.db"
        dest = os.path.join(backup_dir, filename)

        shutil.copy2(db_path, dest)

        self.update_title_with_backup_info()

    # ---------------------------------------------------------
    # Clear-knop activeren/deactiveren
    # ---------------------------------------------------------
    def update_clear_button(self):
        try:
            stock = int(self.stock_var.get())
        except (ValueError, TypeError):
            stock = None

        if stock == 0:
            self.clear_btn.config(state="normal")
        else:
            self.clear_btn.config(state="disabled")

    # ---------------------------------------------------------
    # Zoeken op ALLE velden, case-insensitive
    # ---------------------------------------------------------
    def search(self):
        zoek = self.search_var.get().strip()
        cur = self.conn.cursor()

        if zoek == "":
            cur.execute("SELECT id, locatie, compnr, name, stock FROM components ORDER BY locatie")
        else:
            z = f"%{zoek.upper()}%"
            cur.execute("""
                SELECT id, locatie, compnr, name, stock
                FROM components
                WHERE
                    UPPER(locatie) LIKE ?
                    OR UPPER(compnr) LIKE ?
                    OR UPPER(name) LIKE ?
                    OR UPPER(stock) LIKE ?
                    OR UPPER(description) LIKE ?
                    OR UPPER(url) LIKE ?
                ORDER BY locatie
            """, (z, z, z, z, z, z))

        rows = cur.fetchall()
        self.tree.delete(*self.tree.get_children())

        for row in rows:
            rec_id = row[0]
            values = row[1:]
            self.tree.insert("", "end", iid=rec_id, values=values)

        self.apply_stock_colors()
        self.select_first_record()
        self.update_clear_button()

    # ---------------------------------------------------------
    # Records laden
    # ---------------------------------------------------------
    def load_records(self):
        self.tree.delete(*self.tree.get_children())
        cur = self.conn.cursor()
        cur.execute("SELECT id, locatie, compnr, name, stock FROM components ORDER BY locatie")

        for row in cur.fetchall():
            rec_id = row[0]
            values = row[1:]
            self.tree.insert("", "end", iid=rec_id, values=values)

        self.apply_stock_colors()
        self.select_first_record()
        self.update_clear_button()

    # ---------------------------------------------------------
    # Kleurcodes voorraad
    # ---------------------------------------------------------
    def apply_stock_colors(self):
        for item in self.tree.get_children():
            stock = self.tree.set(item, "stock")
            try:
                stock_val = int(stock)
            except (ValueError, TypeError):
                stock_val = 0

            if stock_val == 0:
                self.tree.item(item, tags=("zero",))
            elif stock_val < 10:
                self.tree.item(item, tags=("low",))
            else:
                self.tree.item(item, tags=("normal",))

        self.tree.tag_configure("zero", background="#ffcccc")
        self.tree.tag_configure("low", background="#fff2cc")
        self.tree.tag_configure("normal", background="white")

    # ---------------------------------------------------------
    # Automatisch eerste record selecteren
    # ---------------------------------------------------------
    def select_first_record(self):
        children = self.tree.get_children()
        if children:
            first = children[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.on_select(None)
        else:
            self.on_select(None)

    # ---------------------------------------------------------
    # Selectie uit lijst
    # ---------------------------------------------------------
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.locatie_var.set("")
            self.compnr_var.set("")
            self.name_var.set("")
            self.stock_var.set("")
            self.memo.delete("1.0", "end")
            self.url_var.set("")
            self.update_clear_button()
            # Geen selectie = niets op te slaan
            self.save_btn.config(
                state="disabled",
                bg="#cccccc",
                fg="#666666",
                activebackground="#cccccc",
                activeforeground="#666666"
            )
            return

        rec_id = sel[0]
        cur = self.conn.cursor()
        cur.execute("""
            SELECT locatie, compnr, name, stock, description, url
            FROM components
            WHERE id=?
        """, (rec_id,))
        row = cur.fetchone()

        if row:
            self.locatie_var.set(row[0])
            self.compnr_var.set(row[1] or "")
            self.name_var.set(row[2] or "")
            self.stock_var.set(row[3] if row[3] is not None else "")
            self.memo.delete("1.0", "end")
            self.memo.insert("1.0", row[4] or "")
            self.memo.mark_set("insert", "end-1c")
            self.url_var.set(row[5] or "")

        self.update_clear_button()

        # Nieuwe selectie = nog geen wijzigingen → opslaan-knop grijs
        self.save_btn.config(
            state="disabled",
            bg="#cccccc",
            fg="#666666",
            activebackground="#cccccc",
            activeforeground="#666666"
        )

    # ---------------------------------------------------------
    # Opslaan
    # ---------------------------------------------------------
    def save_record(self):
        sel = self.tree.selection()
        if not sel:
            return  # nooit nieuwe records maken

        rec_id = sel[0]

        locatie = self.locatie_var.get()
        compnr = self.compnr_var.get()
        name = self.name_var.get()
        stock = self.stock_var.get()
        description = self.memo.get("1.0", "end-1c")
        url = self.url_var.get()

        cur = self.conn.cursor()
        cur.execute("""
            UPDATE components
            SET locatie=?, compnr=?, name=?, stock=?, description=?, url=?
            WHERE id=?
        """, (locatie, compnr, name, stock, description, url, rec_id))

        self.conn.commit()
        self.load_records()
        self.tree.selection_set(rec_id)
        self.update_clear_button()

        # Na opslaan → knop weer grijs
        self.save_btn.config(
            state="disabled",
            bg="#cccccc",
            fg="#666666",
            activebackground="#cccccc",
            activeforeground="#666666"
        )

    # ---------------------------------------------------------
    # URL openen
    # ---------------------------------------------------------
    def open_url(self):
        url = self.url_var.get()
        if url:
            webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    app = ComStorApp(root)
    root.mainloop()
