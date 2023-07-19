from flask import request
from src.helpers import *
from src.app import app

@app.route(BASE_PATH + "/find_internal_nodes", methods=["POST"])
def find_internal_nodes_num():
    """
    API Endpoint to find the number of internal nodes in the tree.
    The tree structure should be sent as a JSON array in the request body.
    """
    app.logger.info('Find internal nodes request received')

    data = request.get_json()
    app.logger.debug(f'Request data: {data}')

    tree = data.get('tree')

    # Check if data is a list
    if not isinstance(tree, list):
        app.logger.error('Invalid input received for tree data')
        return errorit({"error": "Invalid input. Expected a list."}, "INVALID_TREE_DATA", 400)

    result = find_internal_nodes(tree)

    if result.get("error"):
        app.logger.error('Finding internal nodes failed')
        app.logger.debug(f'Error details: {result}')
        return errorit(result, "FIND_INTERNAL_NODES_FAILED", 400)
    else:
        app.logger.info('Successfully found internal nodes')
        return responsify(result, {}, 200)

def find_internal_nodes(tree):
    try:
        count = find_internal_nodes_num(tree)
        return {"internal_nodes_count": count}
    except Exception as e:
        return {"error": str(e)}

def find_internal_nodes_num(tree):
    parent_count = [0] * len(tree)
    for node in tree:
        if node != -1:
            parent_count[node] += 1
    return sum(count > 0 for count in parent_count)

