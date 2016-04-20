class DrSEUsError(Exception):
    def __init__(self, type, source=None, returned=None):
        self.type = type
        self.source = source
        self.returned = returned

    def __str__(self):
        string = ''
        if self.source is not None:
            string += '{}: '.format(self.source)
        string += str(self.type)
        if self.returned is not None:
            string += ', returned: {}'.format(self.returned)
        return string
