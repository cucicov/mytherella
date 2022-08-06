import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tkinter import *
from PIL import ImageTk, Image
from tkinter import ttk
import click
import os
from time import perf_counter


dir_path = r'projector/'
start_time = 0
list_all_portraits = True

class DisplayPhotoEventHandler(FileSystemEventHandler):
    def __init__(self, label, watch_file, root):
        self.label = label
        self.watch_file = watch_file
        self.root = root

    def on_any_event(self, event):

        # new seed image added
        if event.src_path.endswith(".png"):
            global list_all_portraits
            if list_all_portraits:
                print("displaying all recorded portraits first")
                amount_to_sleep = 10 / len(os.listdir(dir_path))
                for path in os.listdir(dir_path):
                    filePath = os.path.join(dir_path, path)

                    if os.path.isfile(filePath) and not path.endswith("1.jpg"):
                        self.root.deiconify()
                        try:
                            local_img = ImageTk.PhotoImage(Image.open(filePath).resize((1000, 1000)))
                            self.label.configure(image=local_img)
                            self.label.image = local_img
                            time.sleep(amount_to_sleep)
                        except Exception:
                            pass
                list_all_portraits = False

            # display last portrait and go to animation
            self.root.deiconify()
            try:
                local_img = ImageTk.PhotoImage(Image.open('projector/1.jpg').resize((1000, 1000)))
                self.label.configure(image=local_img)
                self.label.image = local_img
            except Exception:
                pass

        # old images already displayed. start with new images
        elif (not event.is_directory) and (event.event_type == 'closed'):
            print('modified: ' + event.src_path)

            if event.src_path.endswith("/1.jpg"):
                self.root.deiconify()
                try:
                    local_img = ImageTk.PhotoImage(Image.open(self.watch_file).resize((1000, 1000)))
                    self.label.configure(image=local_img)
                    self.label.image = local_img
                except Exception:
                    pass
            else:
                print("fin")
                time.sleep(3.0)
                self.root.withdraw()
                list_all_portraits = True


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--watch_file', required=True, help='File to watch and display')
@click.option('--watch_directory', required=True, help='Directory to watch and display')
def main(watch_file, watch_directory):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    root = Tk()
    root.geometry('1200x1200+200+200')
    root.attributes('-fullscreen', True)
    root.title("AB")
    root.configure(background='black')

    # uncomment this to resize final image.
    try:
        img = ImageTk.PhotoImage(Image.open(watch_file))
        # img = ImageTk.PhotoImage(Image.open('projector/1.jpg'))
        label = ttk.Label(root, image=img, borderwidth=0)
        label.place(x=10, y=10)

        event_handler = DisplayPhotoEventHandler(label, watch_file, root)
        observer = Observer()
        observer.schedule(event_handler, watch_directory, recursive=True)
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
