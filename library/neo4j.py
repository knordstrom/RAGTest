import datetime
from time import strftime
from neo4j import GraphDatabase
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.llms import GPT4All

from library.llm_api import LLM_API

class Neo4j:

    def __init__(self):
        self.driver = Neo4jGraph("bolt://localhost:7687", "neo4j", "thisislocalanyway")

    def close(self):
        self.driver.close()

    def get_schedule(self, email: str, start_time: datetime, end_time: datetime) -> dict:
        query = """
        MATCH (person:Person {email: '""" + email + """'})
        MATCH (event:Event)-[invite:ATTENDS]-(person)
        MATCH (attendee:Person)-[attending:ATTENDS]-(event)
        WHERE event.end >= datetime('""" + start_time.isoformat() + """') AND event.start <= datetime('""" + end_time.isoformat() + """')
        RETURN DISTINCT person.name, person.email, event.name, event.description, event.start, event.end, invite.status, attendee.name, attendee.email, attending.status
        """
        print("Querying Neo4j with: " + query)
        results = self.driver.query(query)
        print("Results were",   results)
        return Neo4j.collate_schedule_response(results)

    
    @staticmethod
    def collate_schedule_response(records):
        def key(record):
            return record['person.name'] + "||" + record['person.email'] + "||" + record['event.name'] + "||" + str(record['event.start']) + "||" + str(record['event.end'])

        collated = {}
        for record in records:
            k = key(record)
            if k not in collated:
                record['attendees'] = []
                record['event.start'] = record['event.start'].isoformat()
                record['event.end'] = record['event.end'].isoformat()
                collated[k] = record
                
            if record['attendee.email'] != record['person.email']:
                collated[k]['attendees'].append({
                    'name': record['attendee.name'],
                    'email': record['attendee.email'],
                    'attending.status': record['attending.status']
                })

        
        response = list(collated.values())
        # return the response sorted on start time
        return sorted(response, key=lambda x: x['event.start'])
        