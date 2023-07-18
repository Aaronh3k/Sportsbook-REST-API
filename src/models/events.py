from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, exc, text
from sqlalchemy.dialects.postgresql import UUID
from src.app import db, app
from src.models.mixins import BaseMixin
from src.helpers import *

class Event(BaseMixin, db.Model):
    __tablename__ = "events"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url_identifier = db.Column(db.String(255), nullable=False, unique=True)
    active = db.Column(db.Boolean, nullable=False, default=False)
    type = db.Column(db.String(50), nullable=False)
    sport_id = db.Column(db.String(50), db.ForeignKey('sports.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    scheduled_start = db.Column(db.DateTime, nullable=False)
    actual_start = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    __table_args__ = (
        CheckConstraint('actual_start >= scheduled_start OR actual_start IS NULL', name='check_actual_scheduled_start'),
        UniqueConstraint('name', 'sport_id', name='unique_name_sport'),
    )

    _validations_ = {
        "name": {"type": "string", "required": True, "min_length": 1, "max_length": 255},
        "url_identifier": {"type": "string", "required": True, "min_length": 1, "max_length": 255},
        "type": {"type": "enum", "required": True, "options": ["preplay", "inplay"]},
        "status": {"type": "enum", "required": True, "options": ["Pending", "Started", "Ended", "Cancelled"]},
        "scheduled_start": {"type": "datetime", "required": True}
    }

    _restrict_in_creation_  = ["id", "active", "created_at", "updated_at"]
    _restrict_in_update_    = ["id", "active", "sport_id", "created_at", "updated_at"]

    
    @staticmethod
    def create_an_event(data):
        """
        Create a new event
        :param data: [object] contains event info in key value pair

        :return [dict]
        """
        app.logger.info('Event creation initiated')

        allowed_columns = list_diff(Event().columns_list(), Event()._restrict_in_creation_)
        insert_data = {}

        for column in allowed_columns:
            if column in data:
                insert_data[column] = data.get(column)

        # Check if the event status is "Started"
        if data['status'] == "Started":
            insert_data['actual_start'] = datetime.utcnow()
        
        insert_data['active'] = False

        app.logger.debug(f'Event data to be inserted: {insert_data}')
        
        result = Event().validate_and_sanitize(insert_data, Event()._restrict_in_creation_)
        print(result)
        if result.get("errors"):
            app.logger.error('Event data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        try:
            sql = """INSERT INTO events({}) VALUES ({})""".format(
                ', '.join(insert_data.keys()),
                ', '.join([':' + k for k in insert_data.keys()])
            )

            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, insert_data, operation="insert")
           
            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Event creation successful')
            return {"message": "Event successfully created"}
        except exc.IntegrityError as e:
            db.session.rollback()
            print(e)
            err = e.orig.diag.message_detail.rsplit(',', 1)[-1]
            app.logger.error('SQL integrity error encountered')
            app.logger.debug(f'Error details: {err.replace(")", "")}')
            return {"error": err.replace(")", "")}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during event creation')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}
    
    @staticmethod
    def get_events(event_id=None, page=None, offset=None, orderby=None, sortby=None, active=None, regex=None):
        """
        Get events data by event_id or get paginated list of events

        :param event_id: [str] events table primary key
        :param page: [int] page number
        :param offset: [int] page offset - number of rows to return
        :param orderby: [int] sort order (-1 for descending, 1 for ascending)
        :param sortby: [str] column to sort by
        :param active: [bool] active state of the event

        :return [dict/list]
        """
        page = page or 1
        offset = offset or 20
        orderby = orderby or "ASC"
        sortby = sortby or "name"
        active_query = ""
        regex_query = ""

        if active is not None:
            active = bool(active)
            active_query = f"active = {active}"

        if regex is not None:
            regex_query = f"(name ~* '{regex}' OR url_identifier ~* '{regex}')"

        if active_query and regex_query:
            active_query = f"WHERE {active_query} AND {regex_query}"
        elif active_query or regex_query:
            active_query = f"WHERE {active_query} {regex_query}"

        app.logger.info('Event retrieval request received')
        app.logger.debug(f'Request parameters - event_id: {event_id}, page: {page}, offset: {offset}, orderby: {orderby}, sortby: {sortby}, active: {active}, regex: {regex}')

        try:
            if not event_id:
                offset = int(offset)
                page = int(page) - 1
                sql = f"SELECT * FROM events {active_query} ORDER BY {sortby} {orderby} LIMIT {offset} OFFSET {page * offset}"
                events = execute_sql_query(db, sql, operation="select")
    
                if not events:
                    return {"events": [], "meta_data": {"event_count": 0, "page_number": page + 1, "page_offset": offset}}

                events_dict = []
                for event in events:
                    scheduled_start = datetime_to_str(event[7], True) if event[7] else None
                    actual_start = datetime_to_str(event[8], True) if event[8] else None
                    created_at = datetime_to_str(event[9], True) if event[9] else None
                    updated_at = datetime_to_str(event[10], True) if event[10] else None
                    
                    event_dict = dict(zip(("id", "name", "url_identifier", "active", "type", "sport_id", "status", "scheduled_start", "actual_start", "created_at", "updated_at"), 
                        (event[0], event[1], event[2], event[3], event[4], event[5], event[6], scheduled_start, actual_start, created_at, updated_at)))

                    event_dict = {k: v for k, v in event_dict.items() if v is not None}
                    
                    events_dict.append(event_dict)

                count_sql = f"SELECT COUNT(*) FROM events {active_query}"
                total_events = execute_sql_query(db, count_sql, operation="select")
                total_events = total_events[0][0] if total_events else 0

                app.logger.info(f'Retrieved {total_events} events')

                return {"events": events_dict, "meta_data": {"event_count": total_events, "page_number": page + 1, "page_offset": offset}}

            else:
                sql = f"SELECT * FROM events WHERE id = :id"
                event = execute_sql_query(db, sql, {"id": event_id}, operation="select", fetchone=True)

                if not event:
                    return None
                
                scheduled_start = datetime_to_str(event[7], True) if event[7] else None
                actual_start = datetime_to_str(event[8], True) if event[8] else None
                created_at = datetime_to_str(event[9], True) if event[9] else None
                updated_at = datetime_to_str(event[10], True) if event[10] else None

                event_dict = dict(zip(("id", "name", "url_identifier", "active", "type", "sport_id", "status", "scheduled_start", "actual_start", "created_at", "updated_at"), 
                    (event[0], event[1], event[2], event[3], event[4], event[5], event[6], scheduled_start, actual_start, created_at, updated_at)))

                event_dict = {k: v for k, v in event_dict.items() if v is not None}

                app.logger.info(f'Retrieved event with id {event_id}')

                return event_dict

        except Exception as e:
            app.logger.error('Event retrieval failed')
            app.logger.debug(f'Error details: {e}, event_id: {event_id}, page: {page}, offset: {offset}')
            return None
    
    @staticmethod
    def update_an_event(event_id, data):
        """
        Update an existing event

        :param event_id: [str] events table primary key
        :param data: [dict] event updating field data

        :return [dict]
        """
        app.logger.info(f'Update event request received for event id: {event_id}')
        app.logger.debug(f'Request data: {data}')

        # Fetch existing event
        existing_event = Event.query.filter_by(id=event_id).first()
        if not existing_event:
            return {"error": "Event not found"}

        if existing_event.status != "Started" and data.get("status") == "Started":
            data["actual_start"] = datetime.utcnow()

        if existing_event.status == "Started" and data.get("status") != "Started":
            data["actual_start"] = None

        allowed_columns = list_diff(Event().columns_list(), Event()._restrict_in_update_)
        update_data = {}

        for column in allowed_columns:
            if column in data:
                update_data[column] = data.get(column)

        app.logger.debug(f'Event data to be updated: {update_data}')

        result = Event().validate_and_sanitize(update_data, Event()._restrict_in_update_)
        if result.get("errors"):
            app.logger.error('Event data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        if update_data:
            try:
                update_data["updated_at"] = datetime.utcnow()

                set_query = ', '.join([f"{column} = :{column}" for column in update_data.keys()])
                update_data["id"] = event_id

                sql = f"""UPDATE events SET {set_query} WHERE id = :id"""
            
                app.logger.info('Executing SQL query')
                operation_result = execute_sql_query(db, sql, update_data, operation="update")
            
                if not operation_result:
                    raise Exception('Failed to execute SQL query')

                db.session.commit()

                app.logger.info('Event update successful')
                return {"message": f"Event successfully updated with id={event_id}"}
            except Exception as e:
                db.session.rollback()
                app.logger.error('Exception encountered during event update')
                app.logger.debug(f'Exception details: {str(e)}')
                return {"error": str(e)}
        else:
            app.logger.info('No valid update fields provided')
            return {"error": "No valid update fields provided"}

    @staticmethod
    def delete_event_permanently(event_id):
        """
        Delete an existing event permanently

        :param event_id: [str] events table primary key

        :return [dict]
        """
        app.logger.info(f'Delete event request received for event id: {event_id}')

        try:
            sql = """DELETE FROM events WHERE id = :id"""
            params = {"id": event_id}
            
            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, params, operation="delete")

            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Event deletion successful')
            return {"message": f"Event successfully deleted with id={event_id}"}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during event deletion')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}