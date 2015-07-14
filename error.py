class DrSEUSError(Exception):
    dut_hanging = 'DUT hanging'
    missing_output = 'Missing output'

    def __init__(self, error_type):
        self.type = error_type
