from globals import Globals
from library.managers import handlers
from library.data.local import weaviate as w
from library.utils import Utils
import warnings
from library.managers.processor_support import ProcessorSupport
from library.models.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from library.data.external.slack import Slack
from library.managers.handlers import Handlers

warnings.simplefilter("ignore", ResourceWarning)

def start():
    import os
    directory = os.path.dirname(os.path.abspath(__file__))
    weave = w.Weaviate()
    handler = Handlers(weave)
    ProcessorSupport.json_file_listen(Globals().root + "resources/slack_response.json", handler.handle_slack_channel)

if __name__ == '__main__':
    start()