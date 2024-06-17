import json

class ScrapeCache:
    def __init__(self, filename: str):
        self.cache = {}
        self.filename = filename
        
    def load(self):
        try:
            with open(self.filename, "r") as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}
        return self

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.cache, f)

    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value):
        self.cache[key] = value

    def clear(self):
        self.cache = {}
        self.save()
