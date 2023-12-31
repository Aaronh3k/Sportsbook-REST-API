from flask import request
from src.models.sports import Sport
from src.helpers import *
from src.app import app
import requests

@app.route(BASE_PATH + "/sports", methods=["POST"])
def create_a_sport():
    """
    Create a new sport
    """
    app.logger.info('Create sport request received')

    data = request.get_json()
    app.logger.debug(f'Request data: {data}')
    
    result = Sport.create_a_sport(data)

    if result.get("error"):
        app.logger.error('Sport creation failed')
        app.logger.debug(f'Error details: {result}')
        return errorit(result, "SPORT_CREATION_FAILED", 400)
    else:
        app.logger.info('Sport successfully created')
        return responsify(result, {}, 201)

@app.route(BASE_PATH + "/sports/<sport_id>", methods=["GET"])
def get_a_sport(sport_id):
    """
    Get a sport's information

    :param sport_id: [str] sports table primary key
    """
    app.logger.info(f'Sport information request received for Sport ID: {sport_id}')

    sport = Sport.get_sports(sport_id)

    if not sport:
        app.logger.error(f'Sport not found for ID: {sport_id}')
        return errorit("No such sport found", "SPORT_NOT_FOUND", 404)
    else:
        app.logger.info(f'Sport information retrieved for ID: {sport_id}')
        return responsify(sport, {})

@app.route(BASE_PATH + "/sports", methods=["GET"])
def get_sports():
    """
    Get many sports' information
    """
    app.logger.info('Get sports request received')

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
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be sport name or createdAt"}, "TAG_ERROR", 400)

        if request.args.get("sortby") == "name":
            sorting_column = "name"
        elif request.args.get("sortby") == "createdAt":
            sorting_column = "created_at"
        else:
            app.logger.warning('Invalid sortby value')
            return errorit({"orderby":"should be 1 for ascending or -1 for descending","sortby":"should be sport name or createdAt"}, "TAG_ERROR", 400)

    if request.args.get("active") is not None:
        active = True if request.args.get("active").lower() == 'true' else False

    if request.args.get("name_or_url_pattern") is not None:
        regex = request.args.get("name_or_url_pattern")

    app.logger.debug(f'Orderby: {orderby}, Sorting column: {sorting_column}, Active: {active}, Regex: {regex}')

    sports = Sport.get_sports(None, request.args.get("page_number"), request.args.get("page_offset"), orderby, sorting_column, active, regex)
    
    if not sports:
        app.logger.info('No sports found')
        return responsify({"sports":[]}, {})
    elif type(sports) is dict:
        app.logger.info('Single sport found')
        return responsify(sports, {}, 200)
    else:
        app.logger.info(f'{len(sports)} sports found')
        return responsify(sports, {})

@app.route(BASE_PATH + "/sports/<id>", methods=["PATCH"])
def update_a_sport(id):
    """
    Update sport information

    :param id: [str] sports table primary key
    """
    data = request.get_json()
    
    result = Sport.update_a_sport(id, data)

    if not result:
        return {"error": "No such sport found", "status": 404}, 404
    elif result.get("error"):
        return {"error": result.get("error"), "status": 400}, 400
    else:
        return responsify(result, {}, 200)
    
@app.route(BASE_PATH + "/sports/<id>", methods=["DELETE"])
def delete_sport_permanently(id):
    """
    Delete a sport permanently

    :param id: [str] sports table primary key
    """
    result = Sport.delete_sport_permanently(id)

    if not result:
        return errorit("No such sport found", "SPORT_NOT_FOUND", 404)

    if result.get("error"):
        return errorit(result, "SPORT_DELETION_FAILED", 400)

    return responsify(result, {}, 200)

import requests

@app.route(BASE_PATH + "/sports/upload_external", methods=["POST"])
def fetch_and_store_sports():
    """
    Fetches sports data from external API and stores it in database
    """
    app.logger.info('Fetch and store sports data request received')

    data = request.get_json()
    no_of_sports = data.get("no_of_sports", 1)
    
    if no_of_sports <= 0:
        return errorit("No of sports to be added must be a positive integer", "INVALID_REQUEST", 400)

    response = requests.get(f'{EX_API}sports?apiKey={EX_API_KEY}')

    if response.status_code == 200:
        sports = response.json()
        if no_of_sports > len(sports):
            return errorit(f"Requested {no_of_sports} sports, but only {len(sports)} available", "TOO_MANY_SPORTS_REQUESTED", 400)

        count_added = 0
        for sport in sports:
            if count_added >= no_of_sports:
                break

            data = {
                "name": sport["group"],
                "url_identifier": sport["key"],
            }
            app.logger.debug(f'Sport data: {data}')

            # Check if sport already exists
            existing_sport = Sport.get_sports(regex=data["name"])
            if existing_sport and existing_sport.get("sports"):
                app.logger.debug('Sport already exists, skipping to next')
                continue

            result = Sport.create_a_sport(data)

            if result.get("error"):
                app.logger.error('Sport creation failed')
                app.logger.debug(f'Error details: {result}')
                return errorit(result, "SPORT_CREATION_FAILED", 400)
            else:
                count_added += 1

        app.logger.info('Sports data successfully fetched and stored')
        return responsify({"message":"Sports data successfully fetched and stored"}, {}, 201)
    else:
        app.logger.error('Failed to fetch sports data from external API')
        return errorit("Failed to fetch sports data from external API", "EXTERNAL_API_ERROR", 500)