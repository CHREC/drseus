class DrSEUSError(Exception):
    hanging = 'Hanging'
    missing_output = 'Missing output'

    def __init__(self, error_type):
        self.type = error_type
