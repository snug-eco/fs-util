#!/bin/python3

import argparse
import struct
import os


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

parser_image = subparsers.add_parser("image", help='image from directory')
parser_image.add_argument('dir', help='directory')

args = parser.parse_args()
sd = open(args.dev, "rb+")

class SdFile:
    header_format = '<B255sLL'
    header_size = struct.calcsize(header_format)
    
    @classmethod
    def parse(cls):
        self = cls()
        self.addr = sd.tell()
        (
            self.flags, 
            name, 
            self.hash,
            self.size,
        ) = struct.unpack(
            self.header_format, 
            sd.read(self.header_size)
        )
        self.name = name.decode('ascii').strip('\0')
        self.content = sd.read(self.size)

        return self

    def valid(self):
        return self.flags in (0xB0, 0xA0)

    def emit(self):
        sd.seek(self.addr)
        header = struct.pack(
            self.header_format,
            self.flags, 
            self.name.encode('ascii'), 
            self.hash, 
            self.size
        )

        sd.write(header)
        sd.write(self.content)

    def __str__(self):
        return f"<file flags={hex(self.flags)} name='{self.name}' size={self.size}>"


def parse_sd_card():
    files = []
    while True:
        file = SdFile.parse()
        if not file.valid(): break
        files.append(file)
    
    #rewind to match before invalid
    sd.seek(file.addr)

    return files

def emit_sd_card(files):
    for file in files:
        file.emit()

def dj2(name):
    hash = 5381

    for char in name:
        hash = ((hash << 5) + hash) + ord(char);

    return hash & 0xFFFFFFFF

def find(files, name):
    targets = [] 
    for file in files:
        if file.name == name:
            targets.append(file)

    return targets




def main():
    files = parse_sd_card()

    match args.command:
        case 'list':
            for file in files:
                print(file)

                if file.hash != dj2(file.name):
                    print("Warning! File name hash mismatch.")
                    print(f"should: {dj2(file.name)} is: {file.hash}")

        case 'upload':
            if len(find(files, args.file)) > 0:
                print("File already exists.")
                return

            else:
                file = SdFile()
                file.name = args.file
                file.size = os.path.getsize(file.name)
                file.hash = dj2(file.name)
                file.addr = sd.tell()
                file.flags = 0xB0

                with open(file.name, 'rb') as f:
                    file.content = f.read()

                files.append(file)

    emit_sd_card(files)






if __name__ == '__main__' :
    main()





