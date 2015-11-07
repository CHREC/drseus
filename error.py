class DrSEUsError(Exception):
    hanging = 'Hanging'
    missing_output = 'Missing output'
    scp_error = 'SCP error'

    def __init__(self, error_type):
        self.type = error_type
