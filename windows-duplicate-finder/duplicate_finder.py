import csv
import hashlib
import os
import queue
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Read-only duplicate finder for Windows. Python 3.10+.
CHUNK = 1024 * 1024

def sha256(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            value.update(block)
    return value.hexdigest()

def find_duplicates(root, update=lambda message: None):
    sizes = defaultdict(list)
    errors = []
    count = 0

    def walk_error(error):
        errors.append(str(error))

    for folder, dirs, filenames in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = [name for name in dirs if not (Path(folder) / name).is_symlink()]
        for name in filenames:
            path = Path(folder) / name
            if path.is_symlink():
                continue
            try:
                sizes[path.stat().st_size].append(path)
                count += 1
                if count % 200 == 0:
                    update(f"Inventerar: {count} filer")
            except OSError as error:
                errors.append(f"{path}: {error}")

    matches = defaultdict(list)
    checked = 0
    for size, paths in sizes.items():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                before = path.stat()
                if before.st_size != size:
                    raise OSError("Filen har ändrat storlek")
                signature = sha256(path)
                after = path.stat()
                if after.st_size != size or after.st_mtime_ns != before.st_mtime_ns:
                    raise OSError("Filen ändrades under sökningen")
                matches[(size, signature)].append(path)
                checked += 1
                if checked % 20 == 0:
                    update(f"Hashar: {checked} filer")
            except OSError as error:
                errors.append(f"{path}: {error}")

    groups = [
        (size, digest, sorted(paths, key=lambda p: str(p).casefold()))
        for (size, digest), paths in matches.items()
        if len(paths) > 1
    ]
    groups.sort(key=lambda entry: (-(len(entry[2]) - 1) * entry[0], str(entry[2][0])))
    return groups, count, errors

def size_text(number):
    value = float(number)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dubblettjägaren")
        self.geometry("1080x650")
        self.folder = tk.StringVar()
        self.status = tk.StringVar(value="Välj en mapp. Programmet raderar aldrig filer.")
        self.events = queue.Queue()
        self.groups = []
        self.running = False
        self.build()
        self.after(100, self.poll)

    def build(self):
        content = ttk.Frame(self, padding=15)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="Dubblettjägaren", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(content, text="Hitta filer med identiskt innehåll – helt lokalt och utan radering.").pack(anchor="w", pady=(0, 14))
        controls = ttk.Frame(content)
        controls.pack(fill="x")
        ttk.Entry(controls, textvariable=self.folder).pack(side="left", fill="x", expand=True)
        ttk.Button(controls, text="Välj mapp", command=self.choose).pack(side="left", padx=6)
        self.search_button = ttk.Button(controls, text="Sök dubbletter", command=self.start)
        self.search_button.pack(side="left")
        self.csv_button = ttk.Button(controls, text="Exportera CSV", command=self.export, state="disabled")
        self.csv_button.pack(side="left", padx=6)
        table = ttk.Frame(content)
        table.pack(fill="both", expand=True, pady=12)
        self.tree = ttk.Treeview(table, columns=("group", "size", "path"), show="headings")
        for column, title, width in (("group", "Grupp", 100), ("size", "Storlek", 110), ("path", "Sökväg", 700)):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width)
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self.open_folder)
        ttk.Label(self, textvariable=self.status, padding=10, wraplength=1050).pack(fill="x")

    def choose(self):
        path = filedialog.askdirectory(title="Välj mapp att söka i")
        if path:
            self.folder.set(path)

    def start(self):
        root = Path(self.folder.get().strip())
        if self.running:
            return
        if not root.is_dir():
            messagebox.showerror("Mapp saknas", "Välj en befintlig mapp.")
            return
        self.running = True
        self.groups = []
        self.tree.delete(*self.tree.get_children())
        self.search_button.config(state="disabled")
        self.csv_button.config(state="disabled")
        self.status.set("Söker...")
        threading.Thread(target=self.worker, args=(root,), daemon=True).start()

    def worker(self, root):
        try:
            result = find_duplicates(root, lambda text: self.events.put(("progress", text)))
            self.events.put(("finished", result))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "progress":
                    self.status.set(value)
                elif kind == "finished":
                    self.finish(*value)
                elif kind == "error":
                    self.running = False
                    self.search_button.config(state="normal")
                    self.status.set("Ett fel uppstod: " + value)
                    messagebox.showerror("Fel", value)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def finish(self, groups, count, errors):
        self.running = False
        self.search_button.config(state="normal")
        self.groups = groups
        duplicates = sum(len(paths) - 1 for _, _, paths in groups)
        bytes_extra = sum(size * (len(paths) - 1) for size, _, paths in groups)
        displayed = 0
        for number, (size, digest, paths) in enumerate(groups, 1):
            for path in paths:
                if displayed >= 5000:
                    break
                self.tree.insert("", "end", values=(number, size_text(size), str(path)))
                displayed += 1
            if displayed >= 5000:
                break
        if groups:
            self.csv_button.config(state="normal")
        info = f"{count} filer undersökta. {len(groups)} grupper, {duplicates} extra kopior. Uppskattat utrymme: {size_text(bytes_extra)}."
        if displayed >= 5000:
            info += " Visar max 5000 rader. CSV innehåller alla."
        if errors:
            info += f" {len(errors)} fel. Exempel: {errors[0]}"
        self.status.set(info)

    def export(self):
        target = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="dubbletter.csv",
                                              filetypes=[("CSV", "*.csv")])
        if not target:
            return
        try:
            with open(target, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Grupp", "Storlek i byte", "SHA256", "Sökväg"])
                for number, (size, digest, paths) in enumerate(self.groups, 1):
                    for path in paths:
                        writer.writerow([number, size, digest, str(path)])
            messagebox.showinfo("Klart", "Resultatet har sparats.")
        except OSError as error:
            messagebox.showerror("Kunde inte exportera", str(error))

    def open_folder(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        path = Path(self.tree.item(selection[0], "values")[2])
        try:
            os.startfile(str(path.parent))
        except OSError as error:
            messagebox.showerror("Kunde inte öppna mappen", str(error))

if __name__ == "__main__":
    App().mainloop()
