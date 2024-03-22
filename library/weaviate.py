import weaviate as w
#import langchain_experimental.text_splitter as lang_splitter
import langchain_text_splitters as lang_splitter
from langchain_community.embeddings import GPT4AllEmbeddings
from library.vdb import VDB 
import weaviate.classes as wvc

class_obj = {
    # Class definition
    "class": "EmailText",

    # Property definitions
    "properties": [
        {
            "name": "text",
            "dataType": ["text"],
        }
    ],

    # Specify a vectorizer
    "vectorizer": "text2vec-gpt4all",

    # Module settings
    "moduleConfig": {
        "text2vec-gpt4all": {
            "vectorizeClassName": False,
            "model": "ada",
            "modelVersion": "002",
            "type": "text"
        },
    },
}


class Weaviate(VDB):

    @property
    def client(self):
        return w.Client(self.url)
    
    def __init__(self, url) -> None:
        self.url = url
        self.create_schema(class_obj)     

    def create_schema(self, schema_object) -> None:
        try:
            self.client.schema.get(schema_object['class'])
        except w.exceptions.UnexpectedStatusCodeError:
            print("Creating new schema " + schema_object['class'] + "...")
            self.client.schema.create_class(schema_object)
    
    def upsert(self, text:str) -> bool:
        values = self.split(text)

        map(lambda x: print(x), values)

        with self.client.batch(
            batch_size=200,  # Specify batch size
            num_workers=2,   # Parallelize the process
        ) as batch:
            for row in values:
                if row.page_content is not None and row.page_content != "":

                    print("Upserting " + str(row))
                    question_object = {
                        "text": row.page_content,
                    }
                    batch.add_data_object(
                        question_object,
                        class_name = class_obj['class'],
                        uuid = w.util.generate_uuid5(question_object)
                    )
                else:
                    print("Skipping row with no content")

        return True
    
    def count(self) -> object:
        return self.client.query.aggregate(class_obj['class']).with_meta_count().do()

    def split(self, text:str) -> list:


        text_splitter = lang_splitter.CharacterTextSplitter(
            separator="\n\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
)
        # text_splitter = lang_splitter.SemanticChunker(GPT4AllEmbeddings())
        return text_splitter.create_documents([text])
    
    def search(self, query:str) -> list:

        # items = self.client.collections.get(class_obj['class'])
        # response = items.query.near_text(
        #     query=query,
        #     limit=5,
        #     # target_vector="title_country",  # Specify the target vector for named vector collections
        #     return_metadata=wvc.query.MetadataQuery(distance=True)
        # )
        print("Querying for " + query + " in " + class_obj['class'] + "...")
        response = (
            self.client.query.get(class_obj['class'], ["text"])
            .with_near_text({
                "concepts": [query]
            })
            .with_limit(2)
            .with_additional(["distance"])
            .do()
        )

        # {'data': {'Get': {'EmailText': [{'distance': 0.0, 'text': 'I do not know the answer to that question.'}]}}}

        return map(lambda x: x['text'], response['data']['Get'][class_obj['class']])
    
    def close(self):
        pass  #the v3 client doesn't have a close method, need to upgrade to invoking 4
#        self.client.close()
