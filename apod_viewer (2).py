#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import io
import datetime
import calendar

API_KEY = "DEMO_KEY"  # Replace with your NASA API key from https://api.nasa.gov

class APODViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NASA APOD Viewer")
        self.geometry("900x600")

        # Toolbar for navigation
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="Search by Date", command=lambda: self.show_frame("date")).pack(side="left", padx=5, pady=5)
        ttk.Button(toolbar, text="Gallery", command=lambda: self.show_frame("gallery")).pack(side="left", padx=5, pady=5)

        # Container for frames
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Initialize frames
        self.frames = {}
        for F in (DateFrame, GalleryFrame):
            frame = F(container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            name = F.__name__.replace("Frame", "").lower()
            self.frames[name] = frame

        self.show_frame("date")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

class DateFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ttk.Label(self, text="Select date:").pack(pady=5)
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        self.date_btn = ttk.Button(self, textvariable=self.date_var, command=self.open_calendar)
        self.date_btn.pack(pady=5)
        ttk.Button(self, text="Fetch", command=self.fetch_apod).pack(pady=5)
        self.title_label = ttk.Label(self, wraplength=700, font=(None, 14, "bold"))
        self.title_label.pack(pady=(10, 0))
        self.image_label = ttk.Label(self)
        self.image_label.pack(pady=10)

    def open_calendar(self):
        CalendarDialog(self, self.date_var)

    def fetch_apod(self):
        date_str = self.date_var.get()
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format")
            return

        url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}&date={date_str}"
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200 or "url" not in data:
            messagebox.showerror("Error", data.get("msg", "Unknown error"))
            return

        img_res = requests.get(data["url"])
        img = Image.open(io.BytesIO(img_res.content))
        img.thumbnail((700, 500))
        photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.title_label.config(text=data.get("title", ""))


class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, variable):
        super().__init__(parent)
        self.variable = variable
        self.title("Select Date")
        self.resizable(False, False)
        self.grab_set()

        selected = datetime.date.fromisoformat(variable.get())
        self.year = selected.year
        self.month = selected.month

        nav = ttk.Frame(self)
        nav.pack(pady=5)
        ttk.Button(nav, text="<", command=self.prev_month).pack(side="left")
        self.header = ttk.Label(nav, text="")
        self.header.pack(side="left", padx=5)
        ttk.Button(nav, text=">", command=self.next_month).pack(side="left")

        self.cal_frame = ttk.Frame(self)
        self.cal_frame.pack(padx=5, pady=5)
        self.update_calendar()

    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.update_calendar()

    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.update_calendar()

    def update_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        self.header.config(text=f"{calendar.month_name[self.month]} {self.year}")
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, d in enumerate(days):
            ttk.Label(self.cal_frame, text=d).grid(row=0, column=i, padx=2, pady=2)

        for r, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.cal_frame, text="").grid(row=r, column=c, padx=1, pady=1)
                else:
                    btn = ttk.Button(
                        self.cal_frame,
                        text=str(day),
                        width=3,
                        command=lambda d=day: self.set_date(d),
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1)

    def set_date(self, day):
        date = datetime.date(self.year, self.month, day)
        self.variable.set(date.isoformat())
        self.destroy()

class GalleryFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5)
        ttk.Button(control_frame, text="Previous", command=lambda: self.change_page(-1)).grid(row=0, column=0, padx=5)
        self.page_label = ttk.Label(control_frame, text="")
        self.page_label.grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Next", command=lambda: self.change_page(1)).grid(row=0, column=2, padx=5)

        # Scrollable canvas for thumbnails
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.scrollable = scrollable

        # Pagination setup
        self.base_date = datetime.date(1995, 6, 16)
        self.today = datetime.date.today()
        self.page_index = 0
        self.load_page()

    def change_page(self, delta):
        new_index = self.page_index + delta
        max_index = ((self.today - self.base_date).days) // 10
        if 0 <= new_index <= max_index:
            self.page_index = new_index
            self.load_page()

    def load_page(self):
        # Clear existing thumbnails
        for widget in self.scrollable.winfo_children():
            widget.destroy()

        start_date = self.base_date + datetime.timedelta(days=self.page_index * 10)
        end_date = min(start_date + datetime.timedelta(days=9), self.today)
        self.page_label.config(text=f"{start_date.isoformat()} → {end_date.isoformat()}")

        url = (
            f"https://api.nasa.gov/planetary/apod"
            f"?api_key={API_KEY}"
            f"&start_date={start_date.isoformat()}"
            f"&end_date={end_date.isoformat()}"
        )
        res = requests.get(url)
        data = res.json()
        images = [item["url"] for item in data if item.get("media_type") == "image"]

        for idx, img_url in enumerate(images):
            try:
                img_res = requests.get(img_url, timeout=10)
                img = Image.open(io.BytesIO(img_res.content))
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                lbl = ttk.Label(self.scrollable, image=photo)
                lbl.image = photo
                lbl.grid(row=idx // 4, column=idx % 4, padx=5, pady=5)
            except Exception as e:
                print(f"Failed to load {img_url}: {e}")

if __name__ == "__main__":
    app = APODViewer()
    app.mainloop()
