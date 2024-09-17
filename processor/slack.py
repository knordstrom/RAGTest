import os

from groq import Groq
import weaviate
from globals import Globals
from library.enums.kafka_topics import KafkaTopics
from library.managers import handlers as h
from library.data.local import weaviate as w
from library.utils import Utils
import warnings
from library.managers.processor_support import ProcessorSupport
from library.models.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from library.data.external.slack import Slack
from library.managers.handlers import Handlers
from kafka.consumer.fetcher import ConsumerRecord

warnings.simplefilter("ignore", ResourceWarning)

def write_slack_to_vdb(slacks: list[ConsumerRecord]):
    db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
    db_port = os.getenv("VECTOR_DB_PORT", "8080")
    print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(slacks)))
    weave: w.Weaviate = None
    print("Received slacks: ", slacks)
    try:
        g = Groq(api_key=os.getenv("GROQ_API_KEY"))
        weave = w.Weaviate(db, db_port)
        handler: h.Handlers = h.Handlers(weave, g)
        # print("number of received documents: ", len(docs))
        for slack in slacks:
            handler.handle_slack_channel(slack.value)
            print(f"slack added ")
    finally:
        if weave is not None:
            weave.close()

def start():
    ProcessorSupport.kafka_listen(KafkaTopics.SLACK, "slack", write_slack_to_vdb)

if __name__ == '__main__':
    start()