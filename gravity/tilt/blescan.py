# BLE iBeaconScanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# JCS 06/07/14
# Adapted for Python3 by Michael duPont 2015-04-05

# BLE scanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# BLE scanner, based on https://code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py

# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertisements
# discovered device

# NOTE: Python's struct.pack() will add padding bytes unless you make the endianness explicit. Little endian
# should be used for BLE. Always start a struct.pack() format string with "<"

#Installation
#sudo apt-get install libbluetooth-dev bluez
#sudo pip-3.2 install pybluez   #pip-3.2 for Python3.2 on Raspberry Pi

import os
import sys
import struct
import bluetooth._bluetooth as bluez

LE_META_EVENT = 0x3e
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_ENABLE=0x000C

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02


def getBLESocket(devID):
    return bluez.hci_open_dev(devID)

#def returnnumberpacket(pkt):
#    myInteger = 0
#    multiple = 256
#    for i in range(len(pkt)):
#        myInteger += struct.unpack("B",pkt[i:i+1])[0] * multiple
#        multiple = 1
#    return myInteger


def returnstringpacket(pkt):
    myString = "";
    for i in range(len(pkt)):
        myString += "%02x" %struct.unpack("B",pkt[i:i+1])[0]
    return myString


#def printpacket(pkt):
#    for i in range(len(pkt)):
#        sys.stdout.write("%02x " % struct.unpack("B",pkt[i:i+1])[0])


def get_packed_bdaddr(bdaddr_string):
    packable_addr = []
    addr = bdaddr_string.split(':')
    addr.reverse()
    for b in addr:
        packable_addr.append(int(b, 16))
    return struct.pack("<BBBBBB", *packable_addr)


def packed_bdaddr_to_string(bdaddr_packed):
    return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))


def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)


def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)


def hci_toggle_le_scan(sock, enable):
    cmd_pkt = struct.pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)


def hci_le_set_scan_parameters(sock):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)


def parse_events(sock, loop_count=100):
    old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    # perform a device inquiry on bluetooth device #0
    # The inquiry should last 8 * 1.28 = 10.24 seconds
    # before the inquiry is performed, bluez should flush its cache of
    # previously discovered devices
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
    myFullList = []
    for i in range(0, loop_count):
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack("BBB", pkt[:3])
        if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
            i = 0
        elif event == bluez.EVT_NUM_COMP_PKTS:
            i = 0
        elif event == bluez.EVT_DISCONN_COMPLETE:
            i = 0
        elif event == LE_META_EVENT:
            subevent, = struct.unpack("B", pkt[3:4])
            pkt = pkt[4:]
            if subevent == EVT_LE_CONN_COMPLETE:
                le_handle_connection_complete(pkt)
            elif subevent == EVT_LE_ADVERTISING_REPORT:
                num_reports = struct.unpack("B", pkt[0:1])[0]
                report_pkt_offset = 0
                for i in range(0, num_reports):
                    # build the return string
                    Adstring = packed_bdaddr_to_string(pkt[report_pkt_offset + 3:report_pkt_offset + 9])
                    Adstring += ',' + returnstringpacket(pkt[report_pkt_offset -22: report_pkt_offset - 6])
                    #Adstring += ',' + "%i" % returnnumberpacket(pkt[report_pkt_offset -6: report_pkt_offset - 4])
                    Adstring += ',' + returnstringpacket(pkt[report_pkt_offset -6: report_pkt_offset - 4])
                    #Adstring += ',' + "%i" % returnnumberpacket(pkt[report_pkt_offset -4: report_pkt_offset - 2])
                    Adstring += ',' + returnstringpacket(pkt[report_pkt_offset -4: report_pkt_offset - 2])
                    try:
                        #Adstring += ',' + "%i" % struct.unpack("b", pkt[report_pkt_offset -2:report_pkt_offset -1])
                        Adstring += ',' + returnstringpacket(pkt[report_pkt_offset -2:report_pkt_offset -1])
                        #The last byte is always 00; we don't really need it
                        #Adstring += ',' + "%i" % struct.unpack("b", pkt[report_pkt_offset -1:report_pkt_offset])
                        #Adstring += ',' + returnstringpacket(pkt[report_pkt_offset -1:report_pkt_offset])
                    except: 1
                    #Prevent duplicates in results
                    if Adstring not in myFullList: myFullList.append(Adstring)
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
    return myFullList

if __name__ == '__main__':
    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        print("ble thread started")
    except:
        print("error accessing bluetooth device...")
        sys.exit(1)

    hci_le_set_scan_parameters(sock)
    hci_enable_le_scan(sock)

    while True:
        returnedList = parse_events(sock, 10)
        print("----------")
        for beacon in returnedList:
            print(beacon)