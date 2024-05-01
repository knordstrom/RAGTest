import re
from urllib.parse import urlparse, urlunparse
import langchain_text_splitters as lang_splitter

class Utils:
    @staticmethod
    def filter_tokens(email: str) -> tuple[str, dict]:
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

