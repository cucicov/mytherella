import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tkinter import *
from PIL import ImageTk, Image
from tkinter import ttk
import click


class DisplayPhotoEventHandler(FileSystemEventHandler):
    def __init__(self, label, watch_file):
        self.label = label
        self.watch_file = watch_file

    def on_any_event(self, event):
        if (not event.is_directory) and (event.event_type == 'closed'):
            print('modified: ' + event.src_path)
            try:
                local_img = ImageTk.PhotoImage(Image.open(self.watch_file).resize((1000, 1000)))
                self.label.configure(image=local_img)
                self.label.image = local_img
            except KeyboardInterrupt:
                pass


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--watch_file', required=True, help='File to watch and display')
def main(watch_file):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    root = Tk()
    root.geometry('1200x1200+4200+4200')
    root.attributes('-fullscreen', True)
    root.title("")
    root.configure(background='black')

    # uncomment this to resize final image.
    try:
        img = ImageTk.PhotoImage(Image.open(watch_file))
        # img = ImageTk.PhotoImage(Image.open('projector/1.jpg'))
        label = ttk.Label(root, image=img, borderwidth=0)
        label.place(x=10, y=10)

        event_handler = DisplayPhotoEventHandler(label, watch_file)
        observer = Observer()
        observer.schedule(event_handler, watch_file, recursive=True)
        observer.start()

        root.mainloop()

    except KeyboardInterrupt:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
