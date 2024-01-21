from serial import Serial
import logging


class Arduino(Serial):
    def __init__(self, port: str, baudrate: int = 9600, commands: list = [], **kwargs) -> None:
        super().__init__(port, baudrate, **kwargs)
        self.commands = commands
        self.logger = logging.getLogger('machine')



    def send_command(self, command: int):
        '''
        Send command to arduino. 
        Can be used to explicitly invoke Arduino operation without calling specific functions \n

        Parameters:
        command (int) : Command to send
        '''
        self.logger.info(f'Sending command to {self.port}: {command}')
        if command in self.commands:
            while True:
                self.write(bytes(str(command)+'\n','utf-8'))
                response = self.get_arduino_response()
                if(response == 'ok'):
                    break
        else:
            raise Exception('Unknown command')
        


    def get_response(self) -> str:
        '''
        Get arduino serial response

        Returns:
        response (str) : Arduino response
        '''
        try:
            response = self.readline().decode('utf-8').rstrip()
        except UnicodeDecodeError:
            response = self.readline().decode('utf-8').rstrip()
        self.logger.info(f'Got response from {self.port}: {response}')
        return response
    

    
    def ping(self) -> bool:
        '''
        Ping arduino

        Returns:
        response (str) : Ping response
        '''
        raise NotImplementedError('Not yet implemented')
    


    def reset_state(self, command: int = 99):
        '''
        Reset arduino state

        Parameters:
        command (int) - Reset command, default to 99
        '''
        self.send_command(command)
        


    def get_uuid(self, command: int = 98) -> str:
        '''
        Try to get arduino uuid

        Parameters:
        command (str) - Get identifier command, default to 98

        Returns:
        identifier (str) - Arduino UUID
        '''
        self.send_command(command)
        uuid = ''
        while True:
            response = self.get_response()
            if response:
                uuid = response
                break
        return uuid
    