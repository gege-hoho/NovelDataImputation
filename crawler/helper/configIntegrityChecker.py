class ConfigIntegrityChecker:
    def __init__(self, config):
        self.config = config

    def check_exists(self, name):
        if not self.config[name]:
            raise Exception(f"no {name} defined")

    def check_int(self, name):
        self.check_exists(name)
        if not type(self.config[name]) is int:
            raise Exception(f"{name} has to be an int")

    def check_float(self, name):
        self.check_exists(name)
        if not type(self.config[name]) is float:
            raise Exception(f"{name} has to be an int")

    def check_set(self, name, values):
        self.check_exists(name)
        if not self.config[name] in values:
            raise Exception(f"mode {self.config[name]} is not known")

    def check_str(self, name):
        self.check_exists(name)
        if not type(self.config[name]) is str:
            raise Exception(f"{name} has to be an str")

    def check_list(self, name):
        self.check_exists(name)
        if not type(self.config[name]) is list:
            raise Exception(f"{name} has to be an list")
