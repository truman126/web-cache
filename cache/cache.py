# cache.py
# written by Truman Johnston, tjohn54@uwo.ca

import socket
import os
import datetime
import signal
import sys

# client connects to cache like server
# cache connects to server
# cache acts as middleman



# Constant for our buffer size

BUFFER_SIZE = 1024

# Constant for the expiry time of files(seconds)
EXPIRY_TIME = 20

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    return message

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'
    
    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break


def save_file_from_socket(sock, bytes_to_read, file_name):
    print('filename in savefile func', file_name)
    with open(file_name, 'wb+') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)
# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def send_error_to_client(sock, code, file_name):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break
# Our main function.

def main():
    
    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    cache_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cache_server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(cache_server_socket.getsockname()[1]))
    cache_server_socket.listen(1)
    
    # Keep the server running forever.
    
    while(1):
        print('Waiting for incoming client connection ...')
        conn, addr = cache_server_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(conn)
        request_list = request.split()

        # to get the server port and host from the request if connection to the server is required

        headers = get_line_from_socket(conn) + '\r\n'
        headers_list = headers.split(':')
        server_host = headers_list[1]
        server_host = server_host.lstrip()
        server_port = headers_list[2].rstrip()

        # If we did not get a GET command respond with a 501.

        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_error_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond with a 505.

        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_error_to_client(conn, '505', '505.html')

        # We have the right request and version, so check if file exists.
                  
        else:

            # If requested file begins with a / we strip it off.
            file_path= req_file = request_list[1]
            # while (req_file[0] == '/'):
            #     req_file = req_file[1:]
            
            file_path = server_host + '_' + str(server_port) + file_path
            dir_list = req_file.split('/')
            dirs = len(dir_list)
            path = ''
            for i in range(dirs-1):
                path +=dir_list[i]
            if path != '':
                path = '/' + path
                
            path = server_host + '_' + str(server_port) + path
            print('path', path)
            if not os.path.exists(path):
                os.makedirs(path)

            req_file = dir_list[dirs-1]
            print('filename = ', req_file)

            # Check if requested file exists and report a 404 if not.

            print(req_file)

            if (not os.path.exists(file_path)) or (os.path.exists(file_path) and os.path.getmtime(file_path) > EXPIRY_TIME):
                print('Requested file does not exist or is expired ... responding with error!')
                
                # cache connects to the server and forwards the original get request
                print('File not found. Attempting to connect to the server')
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(server_host+server_port)
                server_socket.connect((server_host, int(server_port)))

                # recreate the request
                if os.path.exists(file_path) and os.path.getmtime(file_path) > EXPIRY_TIME:
                    print("File expired, attempting to fetch.")
                    date = modification_date(file_path)
                    print('date', date)
                    headers += 'If-Modified-Since: ' + str(date) + '\r\n'
                message = request + '\r\n' + headers + '\r\n'
                server_socket.send(message.encode())

                #receive the file from the server_socket
                response_line = get_line_from_socket(server_socket)
                response_list = response_line.split(' ')
                headers_done = False
                if response_list[1] != '200' and response_list[1] !='304':
                    if response_list[1] == '404':
                        send_error_to_client(conn, '404', '404.html')


                    print('Error:  An error response was received from the server.  Details:\n')
                    print(response_line);
                    bytes_to_read = 0
                    while (not headers_done):
                        header_line = get_line_from_socket(server_socket)
                        print(header_line)
                        header_list = header_line.split(' ')
                        if (header_line == ''):
                            headers_done = True
                        elif (header_list[0] == 'Content-Length:'):
                            bytes_to_read = int(header_list[1])
                # If it's OK, we retrieve and write the file out.

                elif response_list[1] == '304':
                    
                    print('File has not been modified, sending caches version!  Sending file ...')
                    send_response_to_client(conn, '200', file_path)


                else:
                    print('Success:  Server is sending file.  Downloading it now.')

                    # If requested file begins with a / we strip it off.

                    while (req_file[0] == '/'):
                        req_file = req_file[1:]

                    # Go through headers and find the size of the file, then save it.
            
                    bytes_to_read = 0
                    while (not headers_done):
                        header_line = get_line_from_socket(server_socket)
                        header_list = header_line.split(' ')
                        if (header_line == ''):
                            headers_done = True
                        elif (header_list[0] == 'Content-Length:'):
                            bytes_to_read = int(header_list[1])
                    save_file_from_socket(server_socket, bytes_to_read, file_path )


                    # send the file to client from the cache

                    send_response_to_client(conn, '200', file_path)


            # File exists, so prepare to send it!  

            else:
                print(os.path.getmtime(file_path))
                time_elapsed = os.path.getmtime(file_path)
                if EXPIRY_TIME > time_elapsed:
                    print('Requested file good to go!  Sending file ...')
                    send_response_to_client(conn, '200', file_path)
    
                
        # We are all done with this client, so close the connection and
        # Go back to get another one!

    conn.close()
    

if __name__ == '__main__':
    main()




