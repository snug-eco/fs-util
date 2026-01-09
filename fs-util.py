#!/bin/python3

import argparse
import struct
import os

FLAG_ACTIVE = 0xB0
FLAG_DELETE = 0xA0

parser = argparse.ArgumentParser(
    prog='fs-util',
    description='filesystem utilities',
    epilog=':3'
)

parser.add_argument('--dev', '-d',  required=True, help='sd card device name.')
subparsers = parser.add_subparsers(help='operation to perform.', dest='command')

parser_verify = subparsers.add_parser("verify", help='verify image and hashes.')
parser_verify.add_argument('-f', '--fix', action='store_true', help='fix problems if possible.')

subparsers.add_parser("stat", help='statistics.')

parser_upload = subparsers.add_parser("upload", help='upload file')
parser_upload.add_argument('file', help='path to file to upload.')
parser_upload.add_argument('-f', '--force', action='store_true', help='overwrite existing file.')

parser_download = subparsers.add_parser("download", help='download file')
parser_download.add_argument('file', help='path to file to download.')

parser_image = subparsers.add_parser("image", help='image from directory')
parser_image.add_argument('dir', help='directory.')
parser_image.add_argument('-y', '--yes', action='store_true', help='confirm.')


args = parser.parse_args()
sd = open(args.dev, "rb+")

class SdFile:
    header_format = '<B255sLL'
    header_size = struct.calcsize(header_format)
    failed = False
    
    @classmethod
    def parse(cls):
        self = cls()
        (
            self.flags, 
            name, 
            self.hash,
            self.size,
        ) = struct.unpack(
            self.header_format, 
            sd.read(self.header_size)
        )
        try:
            self.name = name.decode('ascii').strip('\0')
            self.content = sd.read(self.size)
        except:
            self.failed = True

        return self

    def valid(self):
        return (not self.failed) and self.flags in (FLAG_ACTIVE, FLAG_DELETE)

    def emit(self):
        header = struct.pack(
            self.header_format,
            self.flags, 
            self.name.encode('ascii'), 
            self.hash, 
            self.size
        )

        sd.write(header)
        sd.write(self.content)

    def from_host(self, path):
        name = os.path.basename(path)
        with open(path, 'rb') as f:
            content = f.read()

        self.name = name
        self.size = os.path.getsize(path)
        self.hash = dj2(name)
        self.flags = FLAG_ACTIVE
        self.content = content

    def __str__(self):
        return f"<file flags={hex(self.flags)} name='{self.name}' size={self.size}>"


def parse_sd_card():
    files = []
    sd.seek(0)
    while True:
        file = SdFile.parse()
        if not file.valid(): break
        files.append(file)

    return files

def emit_sd_card(files):
    sd.seek(0)
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
        if file.name == name and file.flags == FLAG_ACTIVE:
            targets.append(file)

    return targets




def main():
    files = parse_sd_card()

    match args.command:
        case 'verify':
            problems = 0
            print("--- Checking Hashes ---")
            for file in files:
                should = dj2(file.name)
                good = file.hash == should
                print(f"{file}: {'good' if good else 'bad'}")

                if not good:
                    print(f"\tPresent  Hash: {file.hash}")
                    print(f"\tComputed Hash: {should}")
                    
                    if args.fix:
                        file.hash = should
                        print("Fixed hash.")
                    else:
                        problems += 1

            print("--- Checking duplicates ---")
            found = set()
            for file in files:
                good = file not in found
                print(f"{file}: {'good' if good else 'duplicate'}")

                if not good: problems += 1

                found.add(file)

            print()
            print(f"{problems} Problems.")
            if problems == 0: print("Ur gud :3")
            if problems != 0: print("Ur in twubble >:3")


        case 'stat':
            no_files = len(files)
            no_del   = sum(1 for file in files if file.flags == FLAG_DELETE)
            img_size = sd.tell()

            print("--- Stats ---")
            print(f"Image Size             : {img_size} bytes")
            print(f"Number of         files: {no_files}")
            print(f"Number of deleted files: {no_del}")


        case 'upload':
                
            name = os.path.basename(args.file)
            if len(find(files, name)) > 0:
                print("File already exists.")
                if not args.force: return

                print("Overwritting.")
                file = find(files, name)[0]

            else:
                file = SdFile()
                files.append(file)

            file.from_host(args.file)

        case 'image':
            files = []

            for host_file in os.listdir(args.dir):
                sd_file = SdFile()
                files.append(sd_file)
                sd_file.from_host(os.path.join(args.dir, host_file))

            if not args.yes:
                if input("!!you are about to reformat the entire file system!! continue? [y, N] ") != "y":
                    print("aborted.")
                    return

            print("flashing! (byebye data TwT)")


        case 'download':
            fs = find(files, args.file)
            if   len(fs) == 0: print("File {args.file} not found.")
            elif len(fs) >  1: print("Duplicate {args.file}'s found.")
            else:
                src = fs[0]
                with open(args.file, 'wb') as dst:
                    dst.write(src.content)

            #no need for write-back
            return


    emit_sd_card(files)






if __name__ == '__main__' :
    main()





