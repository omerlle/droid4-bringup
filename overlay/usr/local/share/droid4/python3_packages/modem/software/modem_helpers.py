class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
class ModemError(Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg
