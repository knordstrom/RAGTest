from datetime import datetime
import threading
from fastapi import FastAPI
from groq import Groq
from kafka import TopicPartition
import os

import uvicorn
from api import metrics
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

def listen_to_kafka():
    ProcessorSupport.kafka_listen(KafkaTopics.CALENDAR, "calendar_processor", write_events_to_neo4j)

def serve_metrics():
    app = FastAPI(title="Calendar Processor", version="0.1")
    metrics_app = metrics.MetricsApp(app, prefix="calendar_processor", use_kafka=True, use_neo4j=True, use_weaviate=False).make_metrics_app()
    print("Metrics server starting at", metrics_app)

    uvicorn.run(app, host="0.0.0.0", port=5013)

def start_kafka_calendar():
    print("Starting calendar processor...")
    thread = threading.Thread(target = listen_to_kafka)
    thread.daemon = False
    thread.start()

    serve_metrics()
    
    print("Calendar processor started")


if __name__ == '__main__':
    start_kafka_calendar()