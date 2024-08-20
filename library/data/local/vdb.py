class VDB:
    @property
    def client(self):
        pass

    def create_schema(self, schema_object: dict[str,any]) -> None:
        pass
    
    def upsert(self, text:str) -> bool:
        pass
    
    def count(self) -> object:
        pass

    def split(self, text:str) -> list:
        pass

    def search(self, query:str, limit: int = 5) -> list[object]:
        pass
    
    def close(self):
        pass