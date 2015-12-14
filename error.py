class DrSEUsError(Exception):
    hanging = 'Hanging'
    missing_output = 'Missing output'
    scp_error = 'SCP error'
    launch_simics = 'Error launching simics'

    def __init__(self, error_type):
        self.type = error_type

    def __str__(self):
        return str(self.type)
