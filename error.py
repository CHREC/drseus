class DrSEUsError(Exception):
    def __init__(self, *args):
        self.type = args[0]
        super().__init__(*args)
