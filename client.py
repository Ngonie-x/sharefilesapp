# client.py

import shelve
import socket
import os
from kivymd.toast import toast



class Client:
    def __init__(self, host, port, filename, progressbar, file_sent):
        self.host = host
        self.port = port
        self.filename = filename
        self.BUFFER_SIZE = 4096
        self.filesize = os.path.getsize(self.filename)
        self.SEPARATOR = "<SEPARATOR>"
        self.progressbar = progressbar
        self.files_sent = file_sent

    def connect(self):
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting to the server...")
        self.skt.connect((self.host, self.port))
        print("Connected")

        #send the filename and the filesize
        self.skt.send(f"{os.path.basename(self.filename)}{self.SEPARATOR}{self.filesize}".encode())

        self.send_file()

    def send_file(self):
        print("Sending File")
        toast(self.filename)
        self.sent = 0
        with open(self.filename, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(self.BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break

                # we use sendall to assure transmission is busy networks
                self.skt.sendall(bytes_read)

                self.sent += len(bytes_read)
                self.update_progress(self.sent)

        self.skt.close()
        print("Done")
        
        with shelve.open('./save_files/mydata') as shef_file:
            filessent = shef_file['files_sent']
            filessent = str(int(filessent) + 1)
            shef_file['files_sent'] = filessent

        self.files_sent.secondary_text = '[b]Files Sent:[/b]' + filessent
        

    def update_progress(self, bytes_len):
        '''update the progress bar in the UI'''
        bar_value = int((bytes_len/self.filesize)*100)
        self.progressbar.value = bar_value

