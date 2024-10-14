from datetime import datetime
from groq import Groq
from kafka import TopicPartition
import os
from library.data.local import neo4j
from library.models.api_models import MeetingAttendee
from library.enums.kafka_topics import KafkaTopics
from library.managers.processor_support import ProcessorSupport
import library.data.local.weaviate as weaviate
from library.models.weaviate_schemas import Event, WeaviateSchemas
import library.models.event as event
import library.managers.handlers as h
import warnings
from library.data.local import neo4j
from kafka.consumer.fetcher import ConsumerRecord

warnings.simplefilter("ignore", ResourceWarning)

def write_events_to_neo4j(events: list[ConsumerRecord]) -> None:
    graph = neo4j.Neo4j()
    graph.process_events(events)

def start_kafka_calendar():
    ProcessorSupport.kafka_listen(KafkaTopics.CALENDAR, "calendar_processor", write_events_to_neo4j)


if __name__ == '__main__':
    start_kafka_calendar()