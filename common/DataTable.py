import sys, time
from prettytable import PrettyTable

class DataTable:
    def __init__(self) -> None:
        self._headers = ['Name', 'Age', 'University']
        self._extra_lines = 4
        self._data = []
    
    def restart_print(self, numberOfLines):
        for _ in range( numberOfLines + self._extra_lines):
            sys.stdout.write("\x1b[1A\x1b[2K")
    
    def get_headers(self, message):
        return message[0].keys()
    
    def get_data(self, message):
        data = []
        for index in range(len(message)):
            data.append(message[index].values())
        return data
    
    def get_pretty_table(self, data):
        table = PrettyTable(self.get_headers(data))
        table.add_rows(self.get_data(data))
        table.border
        return table
        
    def print_table(self, data):
        table = self.get_pretty_table(data)
        print(table)
        time.sleep(0.3)
        self.restart_print(len(data))
