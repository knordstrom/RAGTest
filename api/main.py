from os import abort
import flask
import context
from library.gmail import Gmail, GmailLogic
from library.llm import LLM, Wizard, Hermes, Falcon, Mini, MistralInstruct, MistralOrca
import library.median as median
import importlib as i
i.reload(median)
import library.weaviate as weaviate

app = flask.Flask(__name__)

@app.route('/median', methods=['GET'])
def get_median() -> str:
    left: str = flask.request.args.get('left')
    right: str = flask.request.args.get('right')

    #Convert the lists of strings to lists of integers
    left_list: list = get_int_list_from_string(left)
    right_list: list = get_int_list_from_string(right)

    print("left_list: " + str(left_list))
    print("right_list: " + str(right_list))

    # Call the public method from the `Solution` class
    result: int = median.Solution().findMedianSortedArrays(left_list, right_list)
    return str(result)

def get_int_list_from_string(string: str) -> list:
    try:
        return list(map(int, get_list_from_string(string)))
    except AttributeError:
        abort(404)

@app.route('/ask', methods=['GET'])
def ask() -> str:
    query = flask.request.args.get('q')
    count = flask.request.args.get('n', None, int)
    if query is not None and query != '':
        w: LLM = MistralInstruct(weaviate.Weaviate("http://127.0.0.1:8080"))
        return w.query(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)
    else:
        flask.abort(404)
        return "No query provided"

@app.route('/email', methods=['GET'])
def email() -> str:
    email = flask.request.args.get('e')
    count = flask.request.args.get('n', None, int)

    if email is not None and email != '':
        mapped: list = read_last_emails(email, count = count)
        write_to_vdb(mapped)
        return mapped
    else:
        flask.abort(404)
        return "No email provided"

def read_last_emails(email: str, count = None) -> list[dict]:
    try:
        g: Gmail = Gmail(email, app.root_path + '/../resources/gmail_creds.json')
        gm: GmailLogic = GmailLogic(g)
        ids = gm.get_emails(count)
        mapped = []
        for id in ids:
            mapped.append(gm.get_email(msg_id=id['id']))
        
        return mapped
    finally:
        g.close()

def write_to_vdb(mapped: list[dict]) -> None:
    print("Writing to VDB..." + str(len(mapped)))
    try:
        w = weaviate.Weaviate("http://127.0.0.1:8080")
        for j,email in enumerate(mapped):
            print("=> Considering email " + str(j) + " of " + str(len(mapped)) + "...")
            try:
                if email['body'] == None or email['body'] == '':
                    email['body'] = email['subject']
                w.upsertChunkedText(email, weaviate.WeaviateSchemas.EMAIL_TEXT, weaviate.WeaviateSchemas.EMAIL, 'body')
            except Exception as e:
                print("Error: " + str(e))
        print(w.count(weaviate.WeaviateSchemas.EMAIL))
    finally:
        w.close()

def get_list_from_string(string: str) -> list:
    if string == None:
        return []
    return list(map(int, string.split(',')))

if __name__ == '__main__':
    app.run()