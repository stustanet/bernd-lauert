from matrix_bot_api.mcommand_handler import MCommandHandler

import json
import ssl
import socket

HELP_DESC = ("!alarm\t\t\t\t\t\t-\tFlash the signal light in the Hackerspace\n"
             "!devices\t\t\t\t\t\t-\tShow # of connected ETH devices in space")

class HackerspaceLink:
    hauptbahnhof_port = 1337
    sstream = None

    def __init__(self, bot):
        alarm_handler = MCommandHandler("alarm", self.alarm_callback)
        device_handler = MCommandHandler("devices", self.dev_callback)
        bot.add_handler(alarm_handler)
        bot.add_handler(device_handler)

    def tls_connect(self):
        """
        Try to establish a TLS connection to the Hauptbahnhof Server.
        """

        # create tls connection to the hauptbahnhof
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_cert_chain('./cert.pem', './key.pem')
        context.load_verify_locations('./trusted.pem')

        s = socket.socket()

        try:
            s.connect(('knecht.stusta.de', self.hauptbahnhof_port))
        except ConnectionRefusedError as e:
            return False

        try:
            self.sstream = context.wrap_socket(s, server_side = False,
                                              server_hostname='Hauptbahnhof')
        except ssl.SSLError as e:
            return False

        return True

    def hauptbahnhof_recv(self, length):
        """
        Try to receive length amount of bytes from the Hauptbahnhof TLS
        connection and return the already interpreted JSON response.
        """
        conn_fail = False
        try:
            resp = self.sstream.recv(length)
        except Exception:
            conn_fail = True

        if (conn_fail or resp == b''):
            print("  [-] Connection to Hauptbahnhof reset. Aborting.")
            self.sstream.close()
            return None

        try:
            jsn = json.loads(resp.decode())
        except json.decoder.JSONDecodeError as e:
            print("  [-] Hauptbahnhof send malformed JSON. Aborting.")
            self.sstream.close()
            return None

        return jsn


    def dev_callback(self, room, event):

        # ignore, if this feature is requested in a private room
        if (event['room_id'] not in TRUSTED_ROOMS):
            room.send_text("This feature is not available in this room")
            return

        if (not self.tls_connect()):
            print("  [-] Couldn't connect to Hauptbahnhof. Aborting alarm.")
            return

        # Try to retrieve the amount of connected ethernet devices
        jsn = {'op': 'GET', 'data': 'DEVICES'}
        self.sstream.send(json.dumps(jsn).encode())

        jsn = self.hauptbahnhof_recv(2048)

        if (jsn):
            if (jsn['state'] == 'FAIL'):
                print("  [-] Hauptbahnof failed to retrieve device number: "
                      + "{}".format(jsn['data']))
                self.sstream.close()
                return
            if (jsn['state'] == 'SUCCESS'):
                num = 'no' if (jsn['msg'] == 0) else jsn['msg']
                text = str("Currently, {} auxiliary ".format(num)
                          +"devices are connected to the Hackerspace network.")
                room.send_text(text)

        # If the receive command failed, error is already printed -> do nothing


    def alarm_callback(self, room, event):

        # ignore, if this feature is requested in a private room
        if (event['room_id'] not in TRUSTED_ROOMS):
            room.send_text("This feature is not available in this room")
            return

        if (not self.tls_connect()):
            print("  [-] Couldn't connect to Hauptbahnhof. Aborting alarm.")
            return

        # Try to trigger the alarm at the hauptbahnhof
        jsn = {'op': 'SET', 'data': 'BULB'}
        self.sstream.send(json.dumps(jsn).encode())

        jsn = self.hauptbahnhof_recv(2048)

        if (jsn):
            if (jsn['state'] == 'FAIL'):
                print("  [-] Hauptbahnof failed to execute alarm command: "
                      + "{}".format(jsn['data']))
                self.sstream.close()
                return

            if (jsn['state'] != 'SUCCESS'):
                room.send_text("Flashing signal lamp in Hackerspace failed")

        # If the receive command failed, error is already printed -> do nothing

def register_to(bot):
    alarm = HackerspaceLink(bot)
