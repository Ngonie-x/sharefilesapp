# server.py
from kivymd.uix.list import OneLineListItem
import socket
import os
import shelve
from kivymd.toast import toast
from kivy.utils import platform
from kivy.clock import mainthread

if platform == 'android':
    import android

    from android.storage import secondary_external_storage_path
    secondary_ext_storage = secondary_external_storage_path()

    from android.permissions import request_permissions, Permission
    request_permissions(
        [
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.ACCESS_NETWORK_STATE,
            Permission.INTERNET
        ]
    )

else:
    secondary_ext_storage = os.getcwd()


def get_server_host():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class Server:
    def __init__(self, progressbar, reception_widget, files_received, saved_in_label, file_location_scroll):
        self.SERVER_HOST = get_server_host()
        self.SERVER_PORT = 5001
        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"
        self.progressbar = progressbar
        self.reception_widget = reception_widget
        self.files_received = files_received
        self.savedlbl = saved_in_label
        self.filelocation = file_location_scroll

    def start_server(self):
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind the socket to our local address
        self.skt.bind((self.SERVER_HOST, self.SERVER_PORT))

        # Enabling our server to listen to connections
        self.skt.listen(1)
        self.display_server_toast()
        print(f'[*] Listening as {self.SERVER_HOST}:{self.SERVER_PORT}')

        # ACCEPT connection if there are any
        client_socket, address = self.skt.accept()

        # is sender connected
        print(f"[+] {address} is connected.")
        # toast(f"{address} is connected")

        # receive file info
        received = client_socket.recv(self.BUFFER_SIZE).decode()
        filename, filesize = received.split(self.SEPARATOR)

        self.change_reception_widget_text(filename)

        # convert filesize to integer
        self.filesize = int(filesize)

        self.receive_the_file(client_socket, filename)

    def receive_the_file(self, client_socket, filename):
        print("Receiving file")
        self.downloaded = 0
        file_path = os.path.join(str(secondary_ext_storage), str(filename))
        self.display_file_toast(file_path)
        with open(file_path, "wb") as f:
            while True:
                # read 1024 bytes from the socekt (receive)
                bytes_read = client_socket.recv(self.BUFFER_SIZE)

                if not bytes_read:
                    # nothing is received since file transmission is done
                    break

                f.write(bytes_read)

                # update progress bar here

                self.downloaded += len(bytes_read)
                self.update_progress(self.downloaded)

        client_socket.close()

        self.skt.close()

        with shelve.open('./save_files/mydata') as shef_file:
            filesreceived = shef_file['files_received']
            filesreceived = str(int(filesreceived) + 1)
            shef_file['files_received'] = filesreceived

        self.file_recieved_ui_changes(filesreceived, file_path)

    @mainthread
    def file_recieved_ui_changes(self, filesreceived, file_path):
        self.files_received.tertiary_text = '[b]Files Received:[/b]' + filesreceived

        saved_in_path = file_path
        self.savedlbl.text = "Saved In"
        self.filelocation.add_widget(OneLineListItem(text=saved_in_path))

        toast("Done")

    @mainthread
    def change_reception_widget_text(self, filename):
        self.reception_widget.text = filename

    @mainthread
    def display_server_toast(self):
        toast(f"Listening on {self.SERVER_HOST}:{self.SERVER_PORT}")

    @mainthread
    def display_file_toast(self, file_path):
        toast(f"{file_path}")

    @mainthread
    def update_progress(self, bytes_len):
        '''update the progress bar in the UI'''
        bar_value = int((bytes_len/self.filesize)*100)
        self.progressbar.value = bar_value
