from flask import request
from src.models.events import Event
from src.helpers import *
from src.app import app

@app.route(BASE_PATH + "/events", methods=["POST"])
def create_an_event():
    """
    Create a new event
    """
    app.logger.info('Create event request received')

    data = request.get_json()
    app.logger.debug(f'Request data: {data}')
    
    result = Event.create_an_event(data)

    if result.get("error"):
        app.logger.error('Event creation failed')
        app.logger.debug(f'Error details: {result}')
        return errorit(result, "EVENT_CREATION_FAILED", 400)
    else:
        app.logger.info('Event successfully created')
        return responsify(result, {}, 201)

@app.route(BASE_PATH + "/events/<event_id>", methods=["GET"])
def get_an_event(event_id):
    """
    Get an event's information

    :param event_id: [str] events table primary key
    """
    app.logger.info(f'Event information request received for Event ID: {event_id}')

    event = Event.get_events(event_id)

    if not event:
        app.logger.error(f'Event not found for ID: {event_id}')
        return errorit("No such event found", "EVENT_NOT_FOUND", 404)
    else:
        app.logger.info(f'Event information retrieved for ID: {event_id}')
        return responsify(event, {})

@app.route(BASE_PATH + "/events", methods=["GET"])
def get_events():
    """
    Get many events' information
    """
    app.logger.info('Get events request received')

    sorting_column = None
    orderby = None
    active = None

    if request.args.get("orderby") and request.args.get("sortby"):
        if request.args.get("orderby") == "1":
            orderby = "ASC"
        elif request.args.get("orderby") == "-1":
            orderby = "DESC"
        else:
            app.logger.warning('Invalid orderby value')
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be event name or createdAt"}, "TAG_ERROR", 400)

        if request.args.get("sortby") == "name":
            sorting_column = "name"
        elif request.args.get("sortby") == "createdAt":
            sorting_column = "created_at"
        else:
            app.logger.warning('Invalid sortby value')
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be event name or createdAt"}, "TAG_ERROR", 400)

    if request.args.get("active") is not None:
        active = True if request.args.get("active").lower() == 'true' else False

    app.logger.debug(f'Orderby: {orderby}, Sorting column: {sorting_column}, Active: {active}')

    events = Event.get_events(None, request.args.get("page_number"), request.args.get("page_offset"), orderby, sorting_column, active)
    
    if not events:
        app.logger.info('No events found')
        return responsify({"events":[]}, {})
    elif type(events) is dict:
        app.logger.info('Single event found')
        return responsify(events, {}, 200)
    else:
        app.logger.info(f'{len(events)} events found')
        return responsify(events, {})

@app.route(BASE_PATH + "/events/<id>", methods=["PATCH"])
def update_an_event(id):
    """
    Update event information

    :param id: [str] events table primary key
    """
    data = request.get_json()
    
    result = Event.update_an_event(id, data)

    if not result:
        return {"error": "No such event found", "status": 404}, 404
    elif result.get("error"):
        return {"error": result.get("error"), "status": 400}, 400
    else:
        return responsify(result, {}, 200)
    
@app.route(BASE_PATH + "/events/<id>", methods=["DELETE"])
def delete_event_permanently(id):
    """
    Delete an event permanently

    :param id: [str] events table primary key
    """
    result = Event.delete_event_permanently(id)

    if not result:
        return errorit("No such event found", "EVENT_NOT_FOUND", 404)

    if result.get("error"):
        return errorit(result, "EVENT_DELETION_FAILED", 400)

    return responsify(result, {}, 200)
