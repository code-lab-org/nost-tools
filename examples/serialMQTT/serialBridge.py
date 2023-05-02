#!/usr/bin/env python3
"""A PyQt5 GUI utility to connect an Arduino with a remote MQTT server."""

################################################################
# Written in 2018-2020 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# standard Python libraries
from __future__ import print_function
import os, sys, struct, time, logging, functools, queue, signal, getpass

# documentation: https://doc.qt.io/qt-5/index.html
# documentation: https://www.riverbankcomputing.com/static/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork, QtSerialPort

# documentation: https://www.eclipse.org/paho/clients/python/docs/
import paho.mqtt.client as mqtt

# configure logging output
log = logging.getLogger('main')
log.setLevel(logging.INFO)

mqtt_log = logging.getLogger('mqtt')
mqtt_log.setLevel(logging.INFO)

paho_log = logging.getLogger('paho.mqtt')
paho_log.setLevel(logging.INFO)

# IDeATE server instances, as per https://mqtt.ideate.cmu.edu/#ports

ideate_ports = { 8884 : '16-223',
                 8885 : '16-375',
                 8886 : '60-223',
                 8887 : '62-362',
                 8889 : '16-376',
}
mqtt_rc_codes = ['Success', 'Incorrect protocol version', 'Invalid client identifier', 'Server unavailable', 'Bad username or password', 'Not authorized']

# Set the version identifier.  This should be updated prior to setting a new git tag.
version_id = 'v1.1'

################################################################
class QtArduinoMQTT(QtCore.QObject):
    """Class to manage a serial connection to an Arduino MQTT sketch using Qt
    QSerialPort object for data transport.  The data protocol is based on lines
    of text.
    """

    # class variable with Qt signal used to communicate between background thread and serial port thread
    _threadedWrite = QtCore.pyqtSignal(bytes, name='threadedWrite')

    def __init__(self, main):
        super(QtArduinoMQTT,self).__init__()
        self._portname = None
        self._buffer = b''
        self._port = None
        self.log = logging.getLogger('arduino')
        self.log.setLevel(logging.INFO)
        self.main = main
        return

    def is_open(self):
        return self._port is not None

    def available_ports(self):
        """Return a list of names of available serial ports."""
        return [port.portName() for port in QtSerialPort.QSerialPortInfo.availablePorts()]

    def set_port(self, name):
        self._portname = name

    def open(self):
        """Open the serial port and initialize communications.  If the port is already
        open, this will close it first.  If the current name is None, this will not open
        anything.  Returns True if the port is open, else False."""
        if self._port is not None:
            self.close()

        if self._portname is None:
            self.log.debug("No port name provided so not opening port.")
            return False

        self._port = QtSerialPort.QSerialPort()
        self._port.setBaudRate(115200)
        self._port.setPortName(self._portname)

        # open the serial port, which should also reset the Arduino
        if self._port.open(QtCore.QIODevice.ReadWrite):
            self.log.info("Opened serial port %s", self._port.portName())
            # always process data as it becomes available
            self._port.readyRead.connect(self.read_input)

            # initialize the slot used to receive data from background threads
            self._threadedWrite.connect(self._data_send)

            return True

        else:
            # Error codes: https://doc.qt.io/qt-5/qserialport.html#SerialPortError-enum
            errcode = self._port.error()
            if errcode == QtSerialPort.QSerialPort.PermissionError:
                self.log.warning("Failed to open serial port %s with a QSerialPort PermissionError, which could involve an already running control process, a stale lock file, or dialout group permissions.", self._port.portName())
            else:
                self.log.warning("Failed to open serial port %s with a QSerialPort error code %d.", self._port.portName(), errcode)
            self._port = None
            return False

    def set_and_open_port(self, name):
        self.set_port(name)
        self.open()

    def close(self):
        """Shut down the serial connection to the Arduino."""
        if self._port is not None:
            self.log.info("Closing serial port %s", self._port.portName())
            self._port.close()
            self._port = None
        return

    def write(self, data):
        if self._port is not None:
            self._port.write(data)
        else:
            self.log.debug("Serial port not open during write.")

    @QtCore.pyqtSlot(bytes)
    def _data_send(self, data):
        """Slot to receive serial data on the main thread."""
        self.write(data)

    def thread_safe_write(self, data):
        """Function to receive data to transmit from a background thread, then send it as a signal to a slot on the main thread."""
        self._threadedWrite.emit(data)

    def read_input(self):
        # Read as much input as available; callback from Qt event loop.
        data = self._port.readAll()
        if len(data) > 0:
            self.data_received(data)
        return

    def _parse_serial_input(self, data):
        # parse a single line of status input provided as a bytestring
        tokens = data.split()
        self.log.debug("Received serial data: %s", tokens)
        self.main.send_arduino_message(data)

    def data_received(self, data):
        # Manage the possibility of partial reads by appending new data to any previously received partial line.
        # The data arrives as a PyQT5.QtCore.QByteArray.
        self._buffer += bytes(data)

        # Process all complete newline-terminated lines.
        while b'\n' in self._buffer:
            first, self._buffer = self._buffer.split(b'\n', 1)
            first = first.rstrip()
            self._parse_serial_input(first)

    def send(self, string):
        self.log.debug("Sending to serial port: %s", string)
        self.write(string.encode()+b'\n')
        return


################################################################
class MainGUI(QtWidgets.QMainWindow):
    """A custom main window which provides all GUI controls.  Requires a delegate main application object to handle user requests."""

    def __init__(self, main, *args, **kwargs):
        super(MainGUI,self).__init__()

        # save the main object for delegating GUI events
        self.main = main

        # create the GUI elements
        self.console_queue = queue.Queue()
        self.setupUi()

        self._handler = None
        self.enable_console_logging()

        # finish initialization
        self.show()

        # manage the console output across threads
        self.console_timer = QtCore.QTimer()
        self.console_timer.timeout.connect(self._poll_console_queue)
        self.console_timer.start(50)  # units are milliseconds

        return

    # ------------------------------------------------------------------------------------------------
    def setupUi(self):
        self.setWindowTitle("IDeATe Arduino-MQTT Bridge " + version_id)
        self.resize(600, 800)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(-1, -1, -1, 9) # left, top, right, bottom

        # help panel button
        help = QtWidgets.QPushButton('Open the Help Panel')
        help.pressed.connect(self.help_requested)
        self.verticalLayout.addWidget(help)

        hrule = QtWidgets.QFrame()
        hrule.setFrameShape(QtWidgets.QFrame.HLine)
        self.verticalLayout.addWidget(hrule)

        # generate fields for configuring the Arduino serial port
        hbox = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Arduino serial port:"))
        self.portSelector = QtWidgets.QComboBox()
        hbox.addWidget(self.portSelector)
        self.update_port_selector()
        self.portSelector.activated['QString'].connect(self.arduino_port_selected)

        rescan = QtWidgets.QPushButton('Rescan Serial Ports')
        rescan.pressed.connect(self.update_port_selector)
        hbox.addWidget(rescan)

        # Arduino connection indicator and connect/disconnect buttons
        hbox = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(hbox)
        self.arduino_connected = QtWidgets.QLabel()
        self.arduino_connected.setLineWidth(3)
        self.arduino_connected.setFrameStyle(QtWidgets.QFrame.Box)
        self.arduino_connected.setAlignment(QtCore.Qt.AlignCenter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.arduino_connected.setSizePolicy(sizePolicy)
        self.set_arduino_connected_state(False)
        hbox.addWidget(self.arduino_connected)
        connect = QtWidgets.QPushButton('Connect')
        connect.pressed.connect(self.main.connect_to_arduino)
        hbox.addWidget(connect)
        disconnect = QtWidgets.QPushButton('Disconnect')
        disconnect.pressed.connect(self.main.disconnect_from_arduino)
        hbox.addWidget(disconnect)

        hrule = QtWidgets.QFrame()
        hrule.setFrameShape(QtWidgets.QFrame.HLine)
        self.verticalLayout.addWidget(hrule)

        # generate GUI for configuring the MQTT connection

        # server name entry and port selection
        hbox = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("MQTT server address:"))
        self.mqtt_server_name = QtWidgets.QLineEdit()
        self.mqtt_server_name.setText(str(self.main.hostname))
        self.mqtt_server_name.editingFinished.connect(self.mqtt_server_name_entered)
        hbox.addWidget(self.mqtt_server_name)

        hbox.addWidget(QtWidgets.QLabel("port:"))
        self.port_selector = QtWidgets.QComboBox()
        hbox.addWidget(self.port_selector)

        self.port_selector.addItem("")
        for pairs in ideate_ports.items():
            self.port_selector.addItem("%d (%s)" % pairs)
        self.port_selector.activated['QString'].connect(self.mqtt_port_selected)

        # attempt to pre-select the stored port number
        try:
            idx = list(ideate_ports.keys()).index(self.main.portnum)
            self.port_selector.setCurrentIndex(idx+1)
        except ValueError:
            pass

        # instructions
        explanation = QtWidgets.QLabel("""Username and password provided by instructor.  Please see help panel for details.""")
        explanation.setWordWrap(True)
        self.verticalLayout.addWidget(explanation)

        # user and password entry
        hbox = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("MQTT username:"))
        self.mqtt_username = QtWidgets.QLineEdit()
        self.mqtt_username.setText(str(self.main.username))
        self.mqtt_username.editingFinished.connect(self.mqtt_username_entered)
        hbox.addWidget(self.mqtt_username)

        hbox.addWidget(QtWidgets.QLabel("password:"))
        self.mqtt_password = QtWidgets.QLineEdit()
        self.mqtt_password.setText(str(self.main.password))
        self.mqtt_password.editingFinished.connect(self.mqtt_password_entered)
        hbox.addWidget(self.mqtt_password)

        # connection indicator
        self.mqtt_connected = QtWidgets.QLabel()
        self.mqtt_connected.setLineWidth(3)
        self.mqtt_connected.setFrameStyle(QtWidgets.QFrame.Box)
        self.mqtt_connected.setAlignment(QtCore.Qt.AlignCenter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.mqtt_connected.setSizePolicy(sizePolicy)
        self.set_mqtt_connected_state(False)

        # connection control buttons
        connect = QtWidgets.QPushButton('Connect')
        connect.pressed.connect(self.connection_requested)
        disconnect = QtWidgets.QPushButton('Disconnect')
        disconnect.pressed.connect(self.main.disconnect_from_mqtt_server)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.mqtt_connected)
        hbox.addWidget(connect)
        hbox.addWidget(disconnect)
        self.verticalLayout.addLayout(hbox)

        hrule = QtWidgets.QFrame()
        hrule.setFrameShape(QtWidgets.QFrame.HLine)
        self.verticalLayout.addWidget(hrule)

        # user and partner ID instructions
        explanation = QtWidgets.QLabel("""Andrew IDs identify where to send and receive messages.  Please see help panel for details.""")
        explanation.setWordWrap(True)
        self.verticalLayout.addWidget(explanation)

        # user ID entry
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Your Andrew ID (for sending):"))
        self.user_id = QtWidgets.QLineEdit()
        self.user_id.setText(self.main.user_id)
        self.user_id.editingFinished.connect(self.user_id_entered)
        hbox.addWidget(self.user_id)
        self.verticalLayout.addLayout(hbox)

        # partner ID entry
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Partner's Andrew ID (for receiving):"))
        self.partner_id = QtWidgets.QLineEdit()
        self.partner_id.setText(self.main.partner_id)
        self.partner_id.editingFinished.connect(self.partner_id_entered)
        hbox.addWidget(self.partner_id)
        self.verticalLayout.addLayout(hbox)

        # text area for displaying both internal and received messages
        self.consoleOutput = QtWidgets.QPlainTextEdit()
        self.consoleOutput.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.verticalLayout.addWidget(self.consoleOutput)

        # instructions
        explanation = QtWidgets.QLabel("""Entering text below will manually send a message.""")
        explanation.setWordWrap(True)
        self.verticalLayout.addWidget(explanation)

        # message payload entry
        hbox = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("User message:")
        self.mqtt_payload = QtWidgets.QLineEdit()
        self.mqtt_payload.setText(self.main.payload)
        self.mqtt_payload.returnPressed.connect(self.mqtt_payload_entered)
        hbox.addWidget(label)
        hbox.addWidget(self.mqtt_payload)
        self.verticalLayout.addLayout(hbox)

        # set up the status bar which appears at the bottom of the window
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # set up the main menu
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 22))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setObjectName("menubar")
        self.menuTitle = QtWidgets.QMenu(self.menubar)
        self.setMenuBar(self.menubar)
        self.actionQuit = QtWidgets.QAction(self)
        self.menuTitle.addAction(self.actionQuit)
        self.menubar.addAction(self.menuTitle.menuAction())
        self.menuTitle.setTitle("File")
        self.actionQuit.setText("Quit")
        self.actionQuit.setShortcut("Ctrl+Q")
        self.actionQuit.triggered.connect(self.quitSelected)

        return

    # --- logging to screen -------------------------------------------------------------
    def enable_console_logging(self):
        # get the root logger to receive all logging traffic
        logger = logging.getLogger()
        # create a logging handler which writes to the console window via self.write
        handler = logging.StreamHandler(self)
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)
        # logger.setLevel(logging.NOTSET)
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
        self._handler = handler
        log.info("Enabled logging in console window.")
        return

    def disable_console_logging(self):
        if self._handler is not None:
            logging.getLogger().removeHandler(self._handler)
            self._handler = None

    # --- window and qt event processing -------------------------------------------------------------
    def show_status(self, string):
        self.statusbar.showMessage(string)

    def _poll_console_queue(self):
        """Write any queued console text to the console text area from the main thread."""
        while not self.console_queue.empty():
            string = str(self.console_queue.get())
            stripped = string.rstrip()
            if stripped != "":
                self.consoleOutput.appendPlainText(stripped)
        return

    def write(self, string):
        """Write output to the console text area in a thread-safe way.  Qt only allows
        calls from the main thread, but the service routines run on separate threads."""
        self.console_queue.put(string)
        return

    def quitSelected(self):
        self.write("User selected quit.")
        self.close()

    def closeEvent(self, event):
        self.write("Received window close event.")
        self.main.app_is_exiting()
        self.disable_console_logging()
        super(MainGUI,self).closeEvent(event)

    def set_mqtt_connected_state(self, flag):
        if flag is True:
            self.mqtt_connected.setText("  Connected   ")
            self.mqtt_connected.setStyleSheet("color: white; background-color: green;")
        else:
            self.mqtt_connected.setText(" Not Connected ")
            self.mqtt_connected.setStyleSheet("color: white; background-color: blue;")

    def set_arduino_connected_state(self, flag):
        if flag is True:
            self.arduino_connected.setText("  Connected   ")
            self.arduino_connected.setStyleSheet("color: white; background-color: green;")
        else:
            self.arduino_connected.setText(" Not Connected ")
            self.arduino_connected.setStyleSheet("color: white; background-color: blue;")

    def update_port_selector(self):
        self.portSelector.clear()
        self.portSelector.addItem("<no port selected>")
        for port in QtSerialPort.QSerialPortInfo.availablePorts():
            self.portSelector.insertItem(0, port.portName())
        self.portSelector.setCurrentText(self.main.portname)

    # --- GUI widget event processing ----------------------------------------------------------------------
    def help_requested(self):
        panel = QtWidgets.QDialog(self)
        panel.resize(600,400)
        panel.setWindowTitle("IDeATe MQTT Monitor: Help Info")
        vbox = QtWidgets.QVBoxLayout(panel)
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text = QtWidgets.QTextEdit(panel)
        hbox.addWidget(text)
        text.insertHtml("""
<style type="text/css">
table { margin-left: 20px; }
td { padding-left: 20px; }
</style>
<a href="#top"></a>
<h1>IDeATe Arduino-MQTT Bridge</h1>

<p>This Python application is a tool intended for connecting an Arduino sketch
to a remote Arduino by passing short data messages back and forth across the
network via a MQTT server.  It supports connecting to an Arduino serial port,
opening an authenticated connection to a remote server, subscribing to a class of
messages in order to receive them, viewing message traffic, and publishing new
messages from the Arduino on a specified message topic.</p>

<p>In typical use, the messages are readable text such as lines of numbers
separated by spaces.  The Arduino serial data is treated as line-delimited text,
with each text line input transmitted as a message.  I.e., messages can be sent
to the remote Arduino using <code>Serial.println()</code>.  Received messages
are treated as text and forwarded to the Arduino with an appended linefeed
character.  Sketches processing the received network data may use Serial.read()
and related functions to parse the input.</p>

<h2>Arduino</h2>

<p>The first set of controls configures the Arduino connection.  The port names
are only scanned during launch so the application will need to be restarted if
the Arduino is plugged in or moved after starting.  Please note this is the raw
list of serial ports which will likely include other non-Arduino devices; when
in doubt, please use the same port name used by the Arduino IDE.</p>

<p>The Arduino USB serial port is shared with the Arduino IDE, so you may need
to disconnect the Arduino IDE Console or stop the Arduino IDE entirely for the
connection to succeed.  You'll also need to disconnect this tool before
reloading code with the IDE.</p>

<h2>Connecting to MQTT</h2>

<p>The next set of controls configures server parameters before attempting a
connection.  Changes will not take effect until the next connection attempt.</p

<dl>
  <dt>server address</dt><dd>The network name of the MQTT server. (Defaults to mqtt.ideate.cmu.edu.)</dd>
  <dt>server port</dt><dd>The numeric port number for the MQTT server.  IDeATe is
      using a separate server for each course, so the drop-down menu also identifies the associated course number.</dd>
  <dt>username</dt><dd>Server-specific identity, chosen by your instructor.</dd>
  <dt>password</dt><dd>Server-specific password, chosen by your instructor.</dd>
</dl>

<p>Your username and password is specific to the MQTT server and will be provided by your instructor.  This may be individual or may be a shared login for all students in the course.  Please note, the password will not be your Andrew password.</p>

<h2>User Identification and Messages</h2>

<p>MQTT works on a publish/subscribe model in which messages are published on
<i>topics</i> identified by a topic name.   For simplicity, this tool publishes your
Arduino output on a single topic based on your Andrew ID; anyone on the server may read this topic to receive your data.
Similarly, this tool <i>subscribes</i> (i.e. listens) to a single topic based on your partner's Andrew ID.
<p>

<p>Changing either the user or partner ID immediately changes what is sent or
received.</p>

<p>The large text field below the ID fieldss is the console area which shows
message traffic as well as status and debugging messages.</p>

<p>At the bottom is a field for publishing a message as if it were received from
your Arduino.<p>

<h2>More Information</h2>

<p>The IDeATE server has more detailed information on the server help page at <b>https://mqtt.ideate.cmu.edu</b></p>

""")
        text.scrollToAnchor("top")
        text.setReadOnly(True)
        panel.show()

    def arduino_port_selected(self, name):
        self.write("Arduino port selected: %s" % name)
        self.main.set_arduino_port(name)

    def mqtt_server_name_entered(self):
        name = self.mqtt_server_name.text()
        self.write("Server name changed: %s" % name)
        self.main.set_server_name(name)

    def decode_port_selection(self):
        title = self.port_selector.currentText()
        if title == "":
            return None
        else:
            return int(title.split()[0])  # convert the first token to a number

    def mqtt_port_selected(self, title):
        portnum  = self.decode_port_selection()
        self.write("Port selection changed: %s" % title)
        self.main.set_server_port(portnum)

    def mqtt_username_entered(self):
        name = self.mqtt_username.text()
        self.write("User name changed: %s" % name)
        self.main.set_username(name)

    def mqtt_password_entered(self):
        name = self.mqtt_password.text()
        self.write("Password changed: %s" % name)
        self.main.set_password(name)

    def connection_requested(self):
        # When the connect button is pressed, make sure all fields are up to
        # date.  It is otherwise possible to leave a text field selected with
        # unreceived changes while pressing Connect.
        hostname = self.mqtt_server_name.text()
        portnum  = self.decode_port_selection()
        username = self.mqtt_username.text()
        password = self.mqtt_password.text()

        self.main.set_server_name(hostname)
        self.main.set_server_port(portnum)
        self.main.set_username(username)
        self.main.set_password(password)

        self.main.connect_to_mqtt_server()

    def user_id_entered(self):
        id = self.user_id.text()
        if id == '':
            log.warning("User ID cannot be empty.")
        else:
            self.main.set_user_id(id)
            self.write("Set user ID to %s" % id)

    def partner_id_entered(self):
        id = self.partner_id.text()
        if id == '':
            log.warning("Partner ID cannot be empty.")
        else:
            self.main.set_partner_id(id)
            self.write("Set partner ID to %s" % id)

    def mqtt_payload_entered(self):
        payload = self.mqtt_payload.text()
        self.main.send_message(payload)
        self.mqtt_payload.clear()

################################################################
class MainApp(object):
    """Main application object holding any non-GUI related state."""

    def __init__(self):

        # Attach a handler to the keyboard interrupt (control-C).
        signal.signal(signal.SIGINT, self._sigint_handler)

        # load any available persistent application settings
        QtCore.QCoreApplication.setOrganizationName("IDeATe")
        QtCore.QCoreApplication.setOrganizationDomain("ideate.cmu.edu")
        QtCore.QCoreApplication.setApplicationName('arduino_mqtt_bridge')
        self.settings = QtCore.QSettings()

        # uncomment to restore 'factory defaults'
        # self.settings.clear()

        # Arduino serial port name
        self.portname = self.settings.value('arduino_port', '')

        # MQTT server settings
        self.hostname = self.settings.value('mqtt_host', 'mqtt.ideate.cmu.edu')
        self.portnum  = self.settings.value('mqtt_port', None)
        self.username = self.settings.value('mqtt_user', 'students')
        self.password = self.settings.value('mqtt_password', '(not yet entered)')

        # Student and partner Andrew IDs, used for generating send and receive message topics.
        username = getpass.getuser()
        self.user_id = self.settings.value('user_id', username)
        self.partner_id = self.settings.value('partner_id', 'unspecified')

        # Create a default subscription and topic based on the username.
        self.subscription = self.partner_id
        self.topic = self.user_id
        self.payload = ''

        # create the interface window
        self.window = MainGUI(self)

        # Initialize the MQTT client system
        self.client = mqtt.Client()
        self.client.enable_logger(paho_log)
        self.client.on_log = self.on_log
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.tls_set()

        # Initialize the Arduino interface system.
        self.arduino = QtArduinoMQTT(self)
        self.arduino.set_port(self.portname)

        self.window.show_status("Disconnected.")
        return

    ################################################################
    def app_is_exiting(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()
        self.arduino.close()

    def _sigint_handler(self, signal, frame):
        print("Keyboard interrupt caught, running close handlers...")
        self.app_is_exiting()
        sys.exit(0)

    ################################################################
    def set_arduino_port(self, name):
        self.settings.setValue('arduino_port', name)
        self.portname = name
        self.arduino.set_port(name)
        return

    def connect_to_arduino(self):
        connected_flag = self.arduino.open()
        self.window.set_arduino_connected_state(connected_flag)
        return

    def disconnect_from_arduino(self):
        self.arduino.close()
        self.window.set_arduino_connected_state(False)
        return

    ################################################################
    def set_server_name(self, name):
        self.hostname = name
        self.settings.setValue('mqtt_host', name)

    def set_server_port(self, value):
        self.portnum = value
        self.settings.setValue('mqtt_port', self.portnum)

    def set_username(self, name):
        self.username = name
        self.settings.setValue('mqtt_user', name)

    def set_password(self, name):
        self.password = name
        self.settings.setValue('mqtt_password', name)

    def connect_to_mqtt_server(self):
        if self.client.is_connected():
            self.window.write("Already connected.")
        else:
            if self.portnum is None:
                log.warning("Please specify the server port before attempting connection.")
            else:
                log.debug("Initiating MQTT connection to %s:%d" % (self.hostname, self.portnum))
                self.window.write("Attempting connection.")
                self.client.username_pw_set(self.username, self.password)
                self.client.connect_async(self.hostname, self.portnum)
                self.client.loop_start()

    def disconnect_from_mqtt_server(self):
        if self.client.is_connected():
            self.client.disconnect()
        else:
            self.window.write("Not connected.")
        self.client.loop_stop()

    ################################################################
    # The callback for when the broker responds to our connection request.
    def on_connect(self, client, userdata, flags, rc):
        mqtt_log.debug("Connected to server with with flags: %s, result code: %s", flags, rc)

        if rc == 0:
            mqtt_log.info("Connection succeeded.")

        elif rc > 0:
            if rc < len(mqtt_rc_codes):
                mqtt_log.warning("Connection failed with error: %s", mqtt_rc_codes[rc])
            else:
                mqtt_log.warning("Connection failed with unknown error %d", rc)

        # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
        client.subscribe(self.subscription)
        self.window.show_status("Connected.")
        self.window.set_mqtt_connected_state(True)
        return

    # The callback for when the broker responds with error messages.
    def on_log(client, userdata, level, buf):
        mqtt_log.debug("level %s: %s", level, userdata)
        return

    def on_disconnect(self, client, userdata, rc):
        mqtt_log.info("Disconnected from server.")
        self.window.show_status("Disconnected.")
        self.window.set_mqtt_connected_state(False)

    # The callback for when a message has been received on a topic to which this
    # client is subscribed.  The message variable is a MQTTMessage that describes
    # all of the message parameters.

    # Some useful MQTTMessage fields: topic, payload, qos, retain, mid, properties.
    #   The payload is a binary string (bytes).
    #   qos is an integer quality of service indicator (0,1, or 2)
    #   mid is an integer message ID.

    def on_message(self, client, userdata, msg):
        printable = self._printable_message_text(msg.payload)
        self.window.write("Received from %s: %s" % (msg.topic, printable))

        if self.arduino.is_open():
            line = msg.payload + b'\n'
            log.debug("Sending received message to Arduino: %s", line)
            self.arduino.thread_safe_write(line)
            log.debug("Sent received message to Arduino: %s", line)
        else:
            log.debug("Arduino not open to receive message: %s", msg.payload)
        return

    def _printable_message_text(self, msg):
        # Test whether the bytes array is 7-bit clean text, else binary, and provide a printable form.
        if all(c > 31 and c < 128 for c in msg):
            return msg.decode(encoding='ascii')
        else:
            return "binary message:" + str([c for c in msg])

    ################################################################
    def set_subscription(self, sub):
        if self.client.is_connected():
            self.client.unsubscribe(self.subscription)
            try:
                self.client.subscribe(sub)
                self.subscription = sub
            except ValueError:
                self.window.write("Invalid subscription string, not changed.")
                self.client.subscribe(self.subscription)
        else:
            self.subscription = sub

    def set_user_id(self, id):
        self.user_id = id
        self.topic = id

    def set_partner_id(self, id):
        self.partner_id = id
        self.set_subscription(id)

    def send_message(self, payload):
        """Publish a message entered by the user."""

        if self.client.is_connected():
            self.client.publish(self.topic, payload)
            self.window.write("Transmitting on %s: %s" % (self.topic, payload))
        else:
            self.window.write("Not connected.")
        self.payload = payload

    def send_arduino_message(self, payload):
        """Transfer a message from the Arduino to the current topic."""
        if self.client.is_connected():
            self.client.publish(self.topic, payload)
            log.debug("Published Arduino message: %s", payload)
            printable = self._printable_message_text(payload)
            self.window.write("Transmitting on %s: %s" % (self.topic, printable))

    ################################################################

def main():
    # Optionally add an additional root log handler to stream messages to the terminal console.
    if False:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        logging.getLogger().addHandler(console_handler)

    # initialize the Qt system itself
    app = QtWidgets.QApplication(sys.argv)

    # create the main application controller
    main = MainApp()

    # run the event loop until the user is done
    log.info("Starting event loop.")
    sys.exit(app.exec_())

################################################################
# Main script follows.  This sequence is executed when the script is initiated from the command line.

if __name__ == "__main__":
    main()