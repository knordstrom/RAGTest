import os


class Globals:

    root: str
    docs_folder: str

    def __new__(cls) -> 'Globals':
        if not hasattr(cls, 'instance'):
            cls.instance = super(Globals, cls).__new__(cls)
            self = cls.instance
            self.root = os.path.dirname(os.path.abspath(__file__))
            self.docs_folder = os.path.join(self.root, "api", "temp")

        return cls.instance
    
    def resource(self, path: str) -> str:
        return os.path.join(self.root, "resources", path)
    
    def test_resource(self, path: str) -> str:
        return os.path.join(self.root, "tests", "resources", path)
    
    def root_resource(self, path: str) -> str:
        return os.path.join(self.root, path)
    
    def api_temp_resource(self, path: str) -> str:
        return os.path.join(self.docs_folder, path)
    