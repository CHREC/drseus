class DrSEUsError(Exception):
    def __init__(self, *args):
        if len(args) > 0:
            self.type = args[0]
        else:
            self.type = None
        if len(args) > 1:
            self.returned = args[1]
        else:
            self.returned = None
        super().__init__(*args)
