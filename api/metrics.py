import os

from kafka import KafkaConsumer

from library.data.local.neo4j import Neo4j
from library.data.local.weaviate import Weaviate
from prometheus_client import CollectorRegistry
from prometheus_client import Histogram

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import FastAPI
from prometheus_client import make_asgi_app

class MetricsApp:
	prefix: str = ""
	WEAVIATE_LATENCY: Histogram = None
	NEO4J_LATENCY: Histogram = None
	KAFKA_LATENCY: Histogram = None
	app: FastAPI = None
	registry = CollectorRegistry()
	weaviate: Weaviate = None

	def __init__(self, app: FastAPI, prefix: str = None, use_kafka: bool = True, use_neo4j: bool = True, use_weaviate: bool = True) -> None:
		self.app = app
		if prefix:
			self.prefix = prefix + "_"
		
		try:
			weave_name = f'{self.prefix}weaviate_request_latency_seconds'
			neo4j_name = f'{self.prefix}neo4j_request_latency_seconds'
			kafka_name = f'{self.prefix}kafka_request_latency_seconds'

			if use_weaviate:
				self.WEAVIATE_LATENCY = Histogram(weave_name, f'Weaviate request latency from {app.title}') 
				self.weaviate = Weaviate()
			if use_neo4j:
				self.NEO4J_LATENCY = Histogram(neo4j_name, f'Neo4j request latency from {app.title}') 
			if use_kafka:
				self.KAFKA_LATENCY = Histogram(kafka_name, f'Kafka request latency from {app.title}')

			print("Created histograms", self.WEAVIATE_LATENCY, self.NEO4J_LATENCY, self.KAFKA_LATENCY)
		except Exception as e:
			print("Error creating histograms", e)
			

	# Using multiprocess collector for registry
	def make_metrics_app(self) -> ASGIApp:
		try:
			if self.WEAVIATE_LATENCY:
				print("Registering weaviate latency", self.WEAVIATE_LATENCY)
				self.registry.register(self.WEAVIATE_LATENCY)
			if self.NEO4J_LATENCY:
				print("Registering neo4j latency", self.NEO4J_LATENCY)
				self.registry.register(self.NEO4J_LATENCY)
			if self.KAFKA_LATENCY:
				print("Registering kafka latency", self.KAFKA_LATENCY)
				self.registry.register(self.KAFKA_LATENCY)
		except Exception as e:
			print("Error registering metrics", e)
		self.metrics()
		metrics_app = make_asgi_app(registry=self.registry)
		self.app.mount("/metrics", metrics_app)
		self.app.add_middleware(MetricsMiddleware, flask_app = self.app, prefix = self.prefix)
		return metrics_app

	def get_kafka_topics(self)-> set[str]:
		if os.getenv("IS_TEST", False):
			return set()
		kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
		consumer = KafkaConsumer(group_id='test', bootstrap_servers=[kafka])
		topics = consumer.topics()
		return topics

	def metrics(self) -> bytes:
		"""Exposes Prometheus metrics."""
		print("Metrics run with ", self.WEAVIATE_LATENCY, self.NEO4J_LATENCY, self.KAFKA_LATENCY)
		if self.WEAVIATE_LATENCY:
			w: Weaviate = Weaviate()  
			w.reset_client()
			with self.WEAVIATE_LATENCY.time(): 
				print("Reaching weaviate")
				_ = w.client
		if self.NEO4J_LATENCY:
			n: Neo4j = Neo4j()
			with self.NEO4J_LATENCY.time():
				print("Reaching neo4j")
				n.connect()
		if self.KAFKA_LATENCY:
			with self.KAFKA_LATENCY.time():
				print("Reaching kafka")
				_ = self.get_kafka_topics() 

class MetricsMiddleware(BaseHTTPMiddleware):
	metrics_app: MetricsApp = None
	def __init__(self, flask_app: FastAPI, app: ASGIApp, prefix: str = None) -> None:
		super().__init__(app)
		self.flask_app = flask_app
		self.metrics_app = MetricsApp(app = self.flask_app, prefix = prefix)

	async def dispatch(self, request, call_next):
		response = await call_next(request)
		if request.url.path.startswith("/metrics"):
			self.metrics_app.metrics()
			print("Metrics Middleware run for request", request.url.path)
		return response