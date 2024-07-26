import datetime
import re
from urllib.parse import urlparse, urlunparse
import langchain_text_splitters as lang_splitter
import neo4j.time

class Utils:
    @staticmethod
    def tokenize_urls(email: str) -> tuple[str, dict]:
        replaced_values = {}
        modified_string = email.replace("\r", "\n")
        modified_string = re.sub(r'[\n]{2,}', '\n', modified_string)

        #token replacement
        urls = re.findall(r"""(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})""", modified_string)
        for url in urls:
            parsed_url = urlparse(url)

            keep = parsed_url.scheme + "://" + parsed_url.netloc
            replace = urlunparse(parsed_url).replace(keep, "")

            token =  "/" + str(len(replaced_values))
            modified_string = modified_string.replace(url, keep + token)
            replaced_values[token] = replace

        return (modified_string, replaced_values)

    @staticmethod
    def is_invite(filename: str) -> bool:
        return filename.endswith(".ics") or filename.endswith(".vcf") or filename.endswith(".vcs")
    
    @staticmethod
    def split(text:str) -> list:
        text_splitter = lang_splitter.RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # text_splitter = lang_splitter.SemanticChunker(GPT4AllEmbeddings())
        return text_splitter.create_documents([text])
    
    @staticmethod
    def isoify(message, key):
        if last_read := message.get(key):
            val = float(last_read)
            if val > 4070989133:
                val = val/1000
            message[key] = Utils.get_iso8601_timestamp(val)

    @staticmethod
    def handle_time(value) -> datetime:
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)
        elif isinstance(value, neo4j.time.DateTime):
            return value.to_native()
        else:
            return value
        
    @staticmethod
    def array_keep_keys(arr, keys):
        return [Utils.dict_keep_keys(d, keys) for d in arr]
    
    @staticmethod
    def dict_keep_keys(d, keys):
        return {k: v for k, v in d.items() if k in keys}
    
    @staticmethod
    def get_iso8601_timestamp(seconds):
        timestamp = datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc)
        return timestamp.isoformat()

    @staticmethod
    def string_multiply(s, n):
        res = ""
        for i in range(n):
            res += s
        return res

    @staticmethod
    def rename_key(d:dict, old_key:str, new_key:str, transform: callable = lambda x: x) -> dict:
        if old_key in d:
            d[new_key] = transform(d.pop(old_key))
        return d
    
    @staticmethod
    def remove_keys(keys: list[list[str]], data: list[dict]) -> list[dict]:
        """Takes a list of keys aad a list of dicts and removes the keys from the dicts in the list
        Args:
            keys (list[list[str]]): A list of lists of strings. Each list of strings is a nested path into the dicts to be deletesd at the leaf node
            data (list[dict]): A list of dicts to remove the keys from"""
        for item in data:   
            #iterate through the list of keys except for the last one, getting the value for the key and defaulting to an empty dict
            for keyvals in keys:
                i = item
                for j in range(len(keyvals) - 1):
                    k = keyvals[j]
                    i = i.get(k, {})
                i.pop(keyvals[-1], None)
        return data