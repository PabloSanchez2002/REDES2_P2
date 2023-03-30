#!/usr/bin/env python
import pika
import psycopg2
import sys
import os

ERROR = 0
OK = 1
REGISTERED = 2


class robot(object):
    def __init__(self) -> None:
        pass




def main():
    contr = robot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
