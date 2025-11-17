#!/bin/python3

import argparse
import struct


parser = argparse.ArgumentParser(
    prog='fs-util',
    description='filesystem utilities',
    epilog=':3'
)

parser.add_argument('--dev', '-d',  required=True, help='sd card device name.')
subparsers = parser.add_subparsers(help='operation to perform.', dest='command')

subparsers.add_parser("list",    help='list file')
subparsers.add_parser("compact", help='run garbage collection')


parser_upload = subparsers.add_parser("upload", help='upload file')
parser_upload.add_argument('file', help='path to file to upload.')

parser_download = subparsers.add_parser("download", help='download file')
parser_download.add_argument('file', help='path to file to download.')

args = parser.parse_args()
sd = open(args.dev, "rb+")

class File:
    header_format = '<B255sLL'
    header_size = struct.calcsize(header_format)

    def __init__(self):
        (
            self.flags, 
            name, 
            self.hash,
            self.size,
        ) = struct.unpack(
            self.header_format, 
            sd.read(self.header_size)
        )
        self.name = name.decode('ascii')
        self.content = sd.read(self.size)

    def valid(self):
        return self.flags in (0xB0, 0xA0)

    def __str__(self):
        return f"<file flags={hex(self.flags)} name='{self.name}' size={self.size}>"


files = []
while True:
    file = File()
    if not file.valid(): break
    files.append(file)


match args.command:
    case 'list':
        for file in files:
            print(file)
        





