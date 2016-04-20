class DrSEUsError(Exception):
    def __init__(self, type, source=None, returned=None):
        self.type = type
        self.source = source
        self.returned = returned

    def __str__(self):
        return '{}{}{}'.format(
            '{}: '.format(self.source) if self.source else '', self.type,
            ', returned: {}'.format(self.returned) if self.returned else '')
