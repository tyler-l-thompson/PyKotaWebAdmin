"""
Created: Aug 15, 2017
Updated: Oct 11, 2018
@author: Tyler Thompson

Note: On Oct 11, 2018 the pykoticon logic was striped and the code simplified.
There was a problem where the postgresql database was not being closed properly.
This caused a number of hanging processes on the server which produced a number of problem.
pyKotaMan.clean() was added to fix this.
"""
from multiprocessing import Pool
from Drivers import Pykota, Logger, Config
import socket
import sys

pyKotaMan = Pykota.Pykota()
config = Config.Config()
log = Logger.Logger(logFile=config.getConfig(key="logFile"), who="Pykotlisten")


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
server_socket.bind(('', int(config.getConfig(key="pykotListenPort"))))
server_socket.settimeout(None)


def main():
        pool = Pool(processes=4)
        while True:
            pool.apply_async(listen())


def listen():
    """
    Description: Socket listener
    Usage: listen()
    Parameters: None
    Returns: None
    """
    client_ip = None
    user_name = None
    try:
        server_socket.listen(5)
        connection, address = server_socket.accept()
        client_ip = str(address[0])
        user_name = connection.recv(1024).strip()
        if not user_name:
            return

        pyKotaMan.deferredInit()
        users = pyKotaMan.getAllUsers()

        balance = None
        for user in users:
            if user_name == user.Name:
                balance = user.AccountBalance

        try:
            connection.sendall(str(balance))
        except:
            log.log(
                message="Error when processing user {0} from ip {1}: {2}".format(user_name, client_ip, str(sys.exc_info())))
            pass

        pyKotaMan.clean()

    except KeyboardInterrupt:
        pyKotaMan.clean()
        sys.exit(0)

    except:
        log.log(
            message="Error when processing user {0} from ip {1}: {2}".format(user_name, client_ip, str(sys.exc_info())))
        pyKotaMan.clean()
        pass


if __name__ == '__main__':
    main()
