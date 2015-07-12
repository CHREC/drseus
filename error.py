class DrSEUSError(Exception):
    dut_hanging = 'DUT hanging'
    missing_output = 'Missing output'

    def __init__(self, error_type, console_buffer=None):
        self.type = error_type
        self.console_buffer = console_buffer
