import socket
import struct

class client:
    
    BUFFER_SIZE = 10000 * 8

    def __init__(self,port):
        # Server information
        self.server_address = 'localhost'
        self.server_port = port

    # Connect to the server
    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_address, self.server_port))

    # Disconnect from the server
    def disconnect(self):
        self.client_socket.close( )

    # Function to send data
    def send(self, cmd, data, type):
        buffer = bytearray(self.BUFFER_SIZE)
        buffer[:8], buffer[8:16] = struct.pack('d', cmd), struct.pack('d', len(data))
        for i in range( len( data ) ):
            buffer[16+i*8:16+(i+1)*8] = struct.pack( type, data[i] )
        self.client_socket.sendall(buffer)

    # Function to receive data
    def receive(self, type):
        buffer = self.client_socket.recv(self.BUFFER_SIZE)
        
        try:
            buffer_size = int(struct.unpack(type, buffer[:8])[0])
        except: 
            buffer_size = 0

        data = [ ]
        for i in range( buffer_size ):
            data.append( struct.unpack( type, buffer[8+i*8:8+(i+1)*8] )[0] )
        return data


class api:

    def initialize(self, port):
        cmd = 0
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        self.client.receive( 'd' )
        self.client.disconnect()

    def update_segments(self, params, port):
        cmd = 1
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, params, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect()
        return int( data[0] )
    
    def set_data_mode(self, port):
        cmd = 10
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        self.client.receive( 'd' )
        self.client.disconnect()

    def set_extrap_mode(self, port):
        cmd = 11
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        self.client.receive( 'd' )
        self.client.disconnect()

    def get_calculated_segment(self, port, idx):
        cmd = 12
        data = [idx]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect()
        return data
    
    def get_calculated_energies(self, port, idx):
        cmd = 13
        data = [idx]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect()
        return data
    
    def calculate_external_capture(self, port):
        cmd = 5
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        self.client.receive( 'd' )
        self.client.disconnect( )

    def get_data_energies(self, port, idx):
        cmd = 6
        data = [idx]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect( )
        return data

    def get_data_segments(self, port, idx):
        cmd = 7
        data = [idx]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect( )
        return data
    
    def get_data_segments_errors(self, port, idx):
        cmd = 8
        data = [idx]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect( )
        return data
    
    def update_data(self, port):
        cmd = 9
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect( )
        return int( data[0] )
    
    def get_params(self, port):
        cmd = 2
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        params = self.client.receive( 'd' )
        self.client.disconnect( )
        return params
    
    def get_params_fixed(self, port):
        cmd = 4
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        params_fixed = self.client.receive( 'd' )
        self.client.disconnect( )
        return params_fixed
    
    def set_channel_radius(self, port, idx, radius):
        cmd = 14
        data = [idx,radius]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        data = self.client.receive( 'd' )
        self.client.disconnect( )
    
    def get_norms(self, port):
        cmd = 15
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        params = self.client.receive( 'd' )
        self.client.disconnect( )
        return params
    
    def get_norms_errors(self, port):
        cmd = 16
        data = [0]
        self.client = client( port )
        self.client.connect( )
        self.client.send( cmd, data, 'd' )
        params = self.client.receive( 'd' )
        self.client.disconnect( )
        return params