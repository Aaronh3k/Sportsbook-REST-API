from flask import request
from src.models.selections import Selection
from src.helpers import *
from src.app import app
from src.models.events import Event
from src.models.sports import Sport
import requests

@app.route(BASE_PATH + "/selections", methods=["POST"])
def create_a_selection():
    """
    Create a new selection
    """
    app.logger.info('Create selection request received')

    data = request.get_json()
    app.logger.debug(f'Request data: {data}')
    
    result = Selection.create_a_selection(data)

    if result.get("error"):
        app.logger.error('Selection creation failed')
        app.logger.debug(f'Error details: {result}')
        return errorit(result, "SELECTION_CREATION_FAILED", 400)
    else:
        app.logger.info('Selection successfully created')
        return responsify(result, {}, 201)

@app.route(BASE_PATH + "/selections/<selection_id>", methods=["GET"])
def get_a_selection(selection_id):
    """
    Get a selection's information

    :param selection_id: [str] selections table primary key
    """
    app.logger.info(f'Selection information request received for Selection ID: {selection_id}')

    selection = Selection.get_selections(selection_id)

    if not selection:
        app.logger.error(f'Selection not found for ID: {selection_id}')
        return errorit("No such selection found", "SELECTION_NOT_FOUND", 404)
    else:
        app.logger.info(f'Selection information retrieved for ID: {selection_id}')
        return responsify(selection, {})

@app.route(BASE_PATH + "/selections", methods=["GET"])
def get_selections():
    """
    Get many selections' information
    """
    app.logger.info('Get selections request received')

    sorting_column = None
    orderby = None
    active = None
    regex = None

    if request.args.get("orderby") and request.args.get("sortby"):
        if request.args.get("orderby") == "1":
            orderby = "ASC"
        elif request.args.get("orderby") == "-1":
            orderby = "DESC"
        else:
            app.logger.warning('Invalid orderby value')
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be selection name or createdAt"}, "TAG_ERROR", 400)

        if request.args.get("sortby") == "name":
            sorting_column = "name"
        elif request.args.get("sortby") == "createdAt":
            sorting_column = "created_at"
        else:
            app.logger.warning('Invalid sortby value')
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be selection name or createdAt"}, "TAG_ERROR", 400)

    if request.args.get("active") is not None:
        active = True if request.args.get("active").lower() == 'true' else False
    
    if request.args.get("name_pattern") is not None:
        regex = request.args.get("name_pattern")

    app.logger.debug(f'Orderby: {orderby}, Sorting column: {sorting_column}, Active: {active}, Regex: {regex}')

    selections = Selection.get_selections(None, request.args.get("page_number"), request.args.get("page_offset"), orderby, sorting_column, active, regex)
    
    if not selections:
        app.logger.info('No selections found')
        return responsify({"selections":[]}, {})
    elif type(selections) is dict:
        app.logger.info('Single selection found')
        return responsify(selections, {}, 200)
    else:
        app.logger.info(f'{len(selections)} selections found')
        return responsify(selections, {})

@app.route(BASE_PATH + "/selections/<id>", methods=["PATCH"])
def update_a_selection(id):
    """
    Update selection information

    :param id: [str] selections table primary key
    """
    data = request.get_json()
    
    result = Selection.update_a_selection(id, data)

    if not result:
        return {"error": "No such selection found", "status": 404}, 404
    elif result.get("error"):
        return {"error": result.get("error"), "status": 400}, 400
    else:
        return responsify(result, {}, 200)
    
@app.route(BASE_PATH + "/selections/<id>", methods=["DELETE"])
def delete_selection_permanently(id):
    """
    Delete a selection permanently

    :param id: [str] selections table primary key
    """
    result = Selection.delete_selection_permanently(id)

    if not result:
        return errorit("No such selection found", "SELECTION_NOT_FOUND", 404)

    if result.get("error"):
        return errorit(result, "SELECTION_DELETION_FAILED", 400)

    return responsify(result, {}, 200)

@app.route(BASE_PATH + "/selections/upload_external/sports/<sport_id>/events/<event_id>", methods=["POST"])
def fetch_and_store_selections(sport_id, event_id):
    """
    Fetches selections data from external API for a specific event and stores it in database
    """
    app.logger.info('Fetch and store selections data request received for sport id: %s, event id: %s', sport_id, event_id)

    data = request.get_json()
    no_of_selections = data.get("no_of_selections", 2)
    
    if no_of_selections <= 0 or no_of_selections > 2:
        return errorit("No of selections to be added must be a positive integer or less then 3", "INVALID_REQUEST", 400)

    sport = Sport.get_sports(sport_id=sport_id)
    event = Event.get_events(event_id=event_id)
    if not (sport and event):
        app.logger.error('No sport/event found with the provided id')
        return errorit("No sport/event found with the provided id", "INVALID_SPORT_OR_EVENT_ID", 400)

    sport_key = sport["url_identifier"]
    event_key = event["url_identifier"]

    response = requests.get(f'{EX_API}sports/{sport_key}/events/{event_key}/odds?apiKey={EX_API_KEY}&regions=uk,us,eu')

    if response.status_code == 200:
        selection = response.json()

        count_added = 0
        for bookmaker in selection["bookmakers"]:
            for market in bookmaker["markets"]:
                for outcome in market["outcomes"]:
                    if count_added >= no_of_selections:
                        break

                    selection_data = {
                        "name": outcome["name"],
                        "event_id": event_id,
                        "price": outcome["price"],
                        "active": True,
                        "outcome": 'Unsettled'
                    }

                    # Check if selection already exists
                    existing_selection = Selection.get_selections(regex=selection_data["name"])
                    if existing_selection["selections"]:
                        app.logger.debug('Selection already exists, skipping to next')
                        continue

                    app.logger.debug(f'Selection data: {selection_data}')
                    result = Selection.create_a_selection(selection_data)

                    if result.get("error"):
                        app.logger.error('Selection creation failed')
                        app.logger.debug(f'Error details: {result}')
                        return errorit(result, "SELECTION_CREATION_FAILED", 400)
                    else:
                        count_added += 1

        app.logger.info('Selections data successfully fetched and stored')
        return responsify({"message": "Selections data successfully fetched and stored"}, {}, 201)
    else:
        app.logger.error('Failed to fetch selections data from external API')
        return errorit("Failed to fetch selections data from external API", "EXTERNAL_API_ERROR", 500)