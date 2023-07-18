from flask import request
from src.models.events import Event
from src.helpers import *
from src.app import app
import requests
from src.models.sports import Sport
from datetime import datetime

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
    regex = None 

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
    
    if request.args.get("name_or_url_pattern") is not None:
        regex = request.args.get("name_or_url_pattern")

    app.logger.debug(f'Orderby: {orderby}, Sorting column: {sorting_column}, Active: {active}, Regex: {regex}')

    events = Event.get_events(None, request.args.get("page_number"), request.args.get("page_offset"), orderby, sorting_column, active, regex)
    
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

@app.route(BASE_PATH + "/events/upload_external/sports/<sport_id>", methods=["POST"])
def fetch_and_store_events(sport_id):
    """
    Fetches events data from external API for a specific sport and stores it in database
    """
    app.logger.info('Fetch and store events data request received for sport id: %s', sport_id)

    data = request.get_json()
    no_of_events = data.get("no_of_events", 1)
    
    if no_of_events <= 0 or no_of_events > 3:
        return errorit("No of events to be added must be a positive integer and cannot exceed 3", "INVALID_REQUEST", 400)

    # Fetch sport details using provided sport_id
    sport = Sport.get_sports(sport_id=sport_id)
    if not sport:
        app.logger.error('No sport found with the provided id')
        return errorit("No sport found with the provided id", "INVALID_SPORT_ID", 400)

    # Extract the url_identifier from sport details
    sport_key = sport["url_identifier"]

    response = requests.get(f'{EX_API}sports/{sport_key}/odds?apiKey={EX_API_KEY}&regions=uk,us,eu')

    if response.status_code == 200:
        events = response.json()

        if no_of_events > len(events):
            return errorit(f"Requested {no_of_events} events, but only {len(events)} available", "TOO_MANY_EVENTS_REQUESTED", 400)

        count_added = 0
        for event in events:
            if count_added >= no_of_events:
                break

            event_data = {
                "name": event["home_team"] + ' vs ' + event["away_team"],
                "url_identifier": event["id"],
                "type": 'preplay',
                "sport_id": sport_id,
                "status": 'Pending',
                "scheduled_start": datetime.strptime(event["commence_time"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Check if event already exists
            existing_event = Event.get_events(regex=event_data["url_identifier"])
            if existing_event["events"]:
                app.logger.debug('Event already exists, skipping to next')
                continue

            app.logger.debug(f'Event data: {event_data}')
            result = Event.create_an_event(event_data)

            if result.get("error"):
                app.logger.error('Event creation failed')
                app.logger.debug(f'Error details: {result}')
                return errorit(result, "EVENT_CREATION_FAILED", 400)
            else:
                count_added += 1

        app.logger.info('Events data successfully fetched and stored')
        return responsify({"message": "Events data successfully fetched and stored"}, {}, 201)
    else:
        app.logger.error('Failed to fetch events data from external API')
        return errorit("Failed to fetch events data from external API", "EXTERNAL_API_ERROR", 500)
