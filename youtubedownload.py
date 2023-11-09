import tkinter
import customtkinter
import math
import pandas as pd
from pytube import YouTube
from tkinter import messagebox
from tkinter.messagebox import askyesno

## https://www.youtube.com/watch?v=-0c7MhcsdlA
## Exit button
## Cancel button
## Show video name and video length and upload time

def startDownload():
    try:
        ytLink = link.get()        
        ytObject = YouTube(ytLink, on_progress_callback = on_progress)
        video = ytObject.streams.get_highest_resolution()

        video_title.configure(text = ytObject.title)
        video_length.configure(text = str(math.floor(ytObject.length / 60)) + ":" + str((ytObject.length % 60)))
        video_uploaded.configure(text = str(ytObject.publish_date)[0:10])

        #video_date = ytObject.publish_date
        #video_date = str(video_date)[0:10]
        #video_uploaded.configure(text = video_date)

        video.download()
    except:
        warning = messagebox.showwarning(title = "Warning", message = "The URL is invalid")

def on_progress(stream, chunks, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    completion = bytes_downloaded / total_size * 100
    per = str(int(completion))
    
    # Update percentage
    pPercentage.configure(text = per + "%")
    pPercentage.update()

    # Update proress bar
    progressBar.set(float(completion) / 100)

def cancelDownload():
    try:
        ytLink = link.get()
    except:
        ytLink = link.get()

def confirmExit():
    answer = askyesno(title = "Confirmation", message = "Are you sure you want to quit?")

    if answer:
        app.destroy()

# System settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Our app frame
app = customtkinter.CTk()
app.geometry("720x480")
app.title("YouTube downloader")

# Adding UI elements
title = customtkinter.CTkLabel(app, text = "Please insert a YouTube link")
title.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = "ew")

# Link input
url_var = tkinter.StringVar()
link = customtkinter.CTkEntry(app, width = 350, height = 40, textvariable = url_var)
link.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = "ew")

# Progress percentage
pPercentage = customtkinter.CTkLabel(app, text = "0%")
pPercentage.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = "ew")

progressBar = customtkinter.CTkProgressBar(app)
progressBar.set(0)
progressBar.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = "ew")

#Download button
cancel = customtkinter.CTkButton(app, text = "Cancel download", command = cancelDownload)
cancel.grid(row = 4, column = 0, padx = 10, pady = 10, sticky = "ew")

start = customtkinter.CTkButton(app, text = "Start download", command = startDownload)
start.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = "ew")

exit = customtkinter.CTkButton(app, text = "Exit program", command = confirmExit)
exit.grid(row = 4, column = 2, padx = 10, pady = 10, sticky = "ew")

# Video details
video_title_label = customtkinter.CTkLabel(app, text = "Video title:")
video_title_label.grid(row = 5, column = 0, padx = 10, pady = 10, sticky = "ew")

video_title = customtkinter.CTkLabel(app, text = "")
video_title.grid(row = 5, column = 1, padx = 10, pady = 10, sticky = "ew")

video_length_label = customtkinter.CTkLabel(app, text = "Video length:")
video_length_label.grid(row = 6, column = 0, padx = 10, pady = 10, sticky = "ew")

video_length = customtkinter.CTkLabel(app, text = "")
video_length.grid(row = 6, column = 1, padx = 10, pady = 10, sticky = "ew")

video_uploaded_label = customtkinter.CTkLabel(app, text = "Video uploaded:")
video_uploaded_label.grid(row = 7, column = 0, padx = 10, pady = 10, sticky = "ew")

video_uploaded = customtkinter.CTkLabel(app, text = "")
video_uploaded.grid(row = 7, column = 1, padx = 10, pady = 10, sticky = "ew")

# Run app
app.mainloop()