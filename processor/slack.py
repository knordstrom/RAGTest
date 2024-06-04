from library import handlers, weaviate as w
from library.utils import Utils
import warnings
from library.processor_support import ProcessorSupport
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from library.slack import Slack
from library.handlers import Handlers

warnings.simplefilter("ignore", ResourceWarning)

def start():
    import os
    directory = os.path.dirname(os.path.abspath(__file__))
    weave = w.Weaviate()
    handler = Handlers(weave)
    ProcessorSupport.json_file_listen(directory + "/../resources/slack_response.json", handler.handle_slack_channel)

if __name__ == '__main__':
    start()