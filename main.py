import shelve
import server
import client
import socket
from threading import Thread
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
# from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.toast import toast
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
import os
from kivy.utils import platform


if platform == 'android':
    import android
    # Android settings
    from android.storage import primary_external_storage_path
    primary_ext_storage = primary_external_storage_path()
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE,
                        Permission.ACCESS_NETWORK_STATE, Permission.INTERNET])

else:
    primary_ext_storage = os.getcwd()


app_path = os.path.dirname(os.path.abspath(__file__))

# Networking


# shelve files


#--------------------Custom Elements--------------------------#

class DialogContent(MDBoxLayout):
    pass


#------------------------Main App class -----------------------#


class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
        )

        self.dialog = None

    def on_start(self):
        # hostname = socket.gethostname()
        # myipaddress = socket.gethostbyname(hostname)
        # self.root.ids.ipaddress.secondary_text = myipaddress
        self.root.ids.ipaddress.secondary_text = self.get_ip()
        try:
            os.mkdir('save_files')

        except Exception:
            pass

        try:
            with shelve.open('./save_files/mydata') as shelf_file:
                self.root.ids.details_item.secondary_text = f"[b]Files Sent: [/b]{shelf_file['files_sent']}"
                self.root.ids.details_item.tertiary_text = f"[b]Files Received: [/b]{shelf_file['files_received']}"
        except KeyError:
            with shelve.open('./save_files/mydata') as shelf_file:
                shelf_file['files_sent'] = '0'
                shelf_file['files_received'] = '0'
            self.root.ids.details_item.secondary_text = '[b]Files Sent: [/b]0'
            self.root.ids.details_item.tertiary_text = '[b]Files Received: [/b]0'

    def get_ip(self):
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

        # hostname = socket.getfqdn()
        # myipaddress = socket.gethostbyname(hostname)

    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = 'Green'

    def create_server(self):
        self.root.ids.bottomnav.switch_tab('filesharing')
        self.new_server = server.Server(self.root.ids.progress, self.root.ids.reception,
                                        self.root.ids.details_item, self.root.ids.sentreceived, self.root.ids.received)
        try:
            self.server_thread = Thread(target=self.new_server.start_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            toast("Server started")
        except Exception as e:
            toast(e)

    # def on_quit(self):
        # with shelve.open('./save_files/mydata') as shelf_file:
        #     shelf_file['files_sent'] = self.root.ids.details_item.secondary_text.text
        #     shelf_file['files_received'] = self.root.ids.details_item.tertiary_text.text

        # try:
        #     self.new_server.skt.close()
        # except Exception as e:
        #     try:
        #         print(e)
        #         self.new_client.skt.close()
        #     except Exception as e:
        #         print(e)
        #         pass

    #------------------Dialog box-----------------#

    def show_recipient_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Choose Destination",
                type="custom",
                content_cls=DialogContent(),
            )
        self.dialog.open()

    def close_dialog(self):
        self.dialog.dismiss()

    #------------------End Dialog--------------------#

    def switchtab(self):
        self.root.ids.bottomnav.switch_tab('filesharing')

    def toast_ip(self):
        toast("Copied")

    def receiver_ipaddress(self, text):
        self.receiveraddress = text

    #----------------File Manager---------------------------#

    def file_manager_open(self):
        # output manager to the screen
        self.file_manager.show(primary_ext_storage)
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        self.exit_manager()

        try:
            self.switch_tab()
            self.root.ids.reception.text = f"Sending: {os.path.basename(path)}"
            self.new_client = client.Client(
                self.receiveraddress, 5001, path, self.root.ids.progress, self.root.ids.details_item)
            self.client_thread = Thread(target=self.new_client.connect)
            self.client_thread.daemon = True
            self.client_thread.start()
        except Exception as e:
            toast(e)
            with open('myerrorlog.txt', 'w') as f:
                f.write(e)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    #------------------End file manager------------------------#


if __name__ == "__main__":
    app = MainApp()
    app.run()
