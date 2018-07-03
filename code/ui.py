import tkinter as tk
import DetectThread as dt
from tkinter import filedialog
from PIL import Image, ImageTk
import os

class Application(tk.Frame):

    folder_path = 'd:/2dtextures'
    image_records = []
    search_term = ''
    SQLFILE = "imagetable.db"
    conn = None
    cur = None

    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        self.open_db()
        self.det_update_search('')

    def open_db(self):
        self.c, self.conn = dt.open_database(self.SQLFILE)

    def create_widgets(self):
        self.det_btn_go = tk.Button(self, text="Refresh Folder", command=self.det_go).grid(row=2, column=700)
        self.det_brw_folder = tk.Button(self, text="Browse", fg="black", command=self.browse_button).grid(row=1, column=700)

        update_search = self.register(self.det_update_search)

        self.det_txt_search = tk.Entry(self, validate='key', validatecommand=(update_search, '%P')).grid(row=0, column=700)
        self.quit = tk.Button(self, text="QUIT", fg="red", command=root.destroy).grid(row=3, column=700)

    def det_go(self):
        dt.detect_main(self.folder_path)
        self.det_update_search('')

    def browse_button(self):
        self.folder_path = tk.filedialog.askdirectory()

    def det_update_search(self, searchval):
        searchfor = searchval.strip()

        self.c.execute("SELECT * from img_data where img_label like ?", ('%'+searchfor+'%',))
        self.image_records = self.c.fetchall()
        print ("Search: {0} - Found: {1} records".format(searchfor, len(self.image_records)))
        self.update_images()
        return True

    def update_images(self):
        image_count = 0
        columns = 6
        for infile in self.image_records:
            if os.path.isfile(infile[0]) is False:
                continue

            image_count += 1
            r, c = divmod(image_count - 1, columns)
            im = Image.open(infile[0])
            resized = im.resize((100, 100), Image.ANTIALIAS)
            tkimage = ImageTk.PhotoImage(resized)
            myvar = tk.Label(self, image=tkimage, text=infile[0][3:], compound=tk.TOP, wraplength=100)
            myvar.image = tkimage
            myvar.grid(row=r, column=c)

            if image_count > 41:
                break


root = tk.Tk()
root.geometry("1024x960")
app = Application(master=root)
app.mainloop()

