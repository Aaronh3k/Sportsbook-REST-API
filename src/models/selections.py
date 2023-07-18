from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, exc, DECIMAL
from src.app import db, app
from src.models.mixins import BaseMixin
from src.helpers import *

class Selection(BaseMixin, db.Model):
    __tablename__ = "selections"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    event_id = db.Column(db.String(50), ForeignKey('events.id'), nullable=False)
    price = db.Column(DECIMAL(10, 2))
    active = db.Column(db.Boolean, nullable=False)
    outcome = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    __table_args__ = (
        UniqueConstraint('name', 'event_id', name='unique_name_event'),
    )

    _validations_ = {
        "name": {"type": "string", "required": True, "min_length": 1, "max_length": 255},
        "event_id": {"type": "string", "required": True, "min_length": 1, "max_length": 50},
        "price": {"type": "float", "required": False, "min_value": 0.00, "max_value": 50000.00},
        "active": {"type": "boolean", "required": True},
        "outcome": {"type": "enum", "required": True, "options": ["Unsettled", "Void", "Lose", "Win"]},
    }

    _restrict_in_creation_  = ["id", "created_at", "updated_at"]
    _restrict_in_update_    = ["id", "event_id", "created_at", "updated_at"]

    @staticmethod
    def create_a_selection(data):
        """
        Create a new selection entry in the database.

        :param data: [dict] dictionary containing the data of the new selection.

        :return [dict]: Returns a dictionary containing a message of success or an error message.
        """
        app.logger.info('Selection creation initiated')

        allowed_columns = list_diff(Selection().columns_list(), Selection()._restrict_in_creation_)
        insert_data = {}

        for column in allowed_columns:
            if column in data:
                insert_data[column] = data.get(column)

        app.logger.debug(f'Selection data to be inserted: {insert_data}')
        
        result = Selection().validate_and_sanitize(insert_data, Selection()._restrict_in_creation_)
        if result.get("errors"):
            app.logger.error('Selection data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        try:
            sql = """INSERT INTO selections({}) VALUES ({})""".format(
                ', '.join(insert_data.keys()),
                ', '.join([':' + k for k in insert_data.keys()])
            )

            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, insert_data, operation="insert")
           
            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Selection creation successful')
            return {"message": "Selection successfully created"}
        except exc.IntegrityError as e:
            db.session.rollback()
            err = e.orig.diag.message_detail.rsplit(',', 1)[-1]
            app.logger.error('SQL integrity error encountered')
            app.logger.debug(f'Error details: {err.replace(")", "")}')
            return {"error": err.replace(")", "")}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during selection creation')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}

    @staticmethod
    def get_selections(selection_id=None, page=None, offset=None, orderby=None, sortby=None, active=None, regex=None):
        """
        Get selections data by selection_id or get paginated list of selections.

        :param selection_id: [str] selections table primary key.
        :param page: [int] page number, defaults to 1.
        :param offset: [int] page offset - number of rows to return, defaults to 20.
        :param orderby: [str] sort order ("ASC" for ascending, "DESC" for descending), defaults to "ASC".
        :param sortby: [str] column to sort by, defaults to "name".
        :param active: [bool] active state of the selection, optional.
        :param regex: [str] regex pattern to search for in 'name', optional.

        :return [dict/list]: Returns either a list of dictionaries representing each selection, or a single dictionary if a selection_id was given.
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
            regex_query = f"(name ~* '{regex}')"

        if active_query and regex_query:
            active_query = f"WHERE {active_query} AND {regex_query}"
        elif active_query or regex_query:
            active_query = f"WHERE {active_query} {regex_query}"

        app.logger.info('Selection retrieval request received')
        app.logger.debug(f'Request parameters - selection_id: {selection_id}, page: {page}, offset: {offset}, orderby: {orderby}, sortby: {sortby}, active: {active}, regex: {regex}')

        try:
            if not selection_id:
                offset = int(offset)
                page = int(page) - 1
                sql = f"SELECT * FROM selections {active_query} ORDER BY {sortby} {orderby} LIMIT {offset} OFFSET {page * offset}"
                selections = execute_sql_query(db, sql, operation="select")
                
                if not selections:
                    return {"selections": [], "meta_data": {"selection_count": 0, "page_number": page + 1, "page_offset": offset}}

                selections_dict = []
                for selection in selections:
                    created_at = datetime_to_str(selection[6], True) if selection[6] else None
                    updated_at = datetime_to_str(selection[7], True) if selection[7] else None

                    selection_dict = dict(zip(("id", "name", "event_id", "price", "active", "outcome", "created_at", "updated_at"), 
                        (selection[0], selection[1], selection[2], selection[3], selection[4], selection[5], created_at, updated_at)))

                    selection_dict = {k: v for k, v in selection_dict.items() if v is not None}
                    
                    selections_dict.append(selection_dict)

                count_sql = f"SELECT COUNT(*) FROM selections {active_query}"
                total_selections = execute_sql_query(db, count_sql, operation="select")
                total_selections = total_selections[0][0] if total_selections else 0

                app.logger.info(f'Retrieved {total_selections} selections')

                return {"selections": selections_dict, "meta_data": {"selection_count": total_selections, "page_number": page + 1, "page_offset": offset}}

            else:
                sql = f"SELECT * FROM selections WHERE id = :id"
                selection = execute_sql_query(db, sql, {"id": selection_id}, operation="select", fetchone=True)

                if not selection:
                    return None

                created_at = datetime_to_str(selection[6], True) if selection[6] else None
                updated_at = datetime_to_str(selection[7], True) if selection[7] else None

                selection_dict = dict(zip(("id", "name", "event_id", "price", "active", "outcome", "created_at", "updated_at"), 
                    (selection[0], selection[1], selection[2], selection[3], selection[4], selection[5], created_at, updated_at)))

                selection_dict = {k: v for k, v in selection_dict.items() if v is not None}

                app.logger.info(f'Retrieved selection with id {selection_id}')

                return selection_dict

        except Exception as e:
            app.logger.error('Selection retrieval failed')
            app.logger.debug(f'Error details: {e}, selection_id: {selection_id}, page: {page}, offset: {offset}')
            return None

    @staticmethod
    def update_a_selection(selection_id, data):
        """
        Update an existing selection entry in the database.

        :param selection_id: [str] the id of the selection to update.
        :param data: [dict] dictionary containing the updated data of the selection.

        :return [dict]: Returns a dictionary containing a message of success or an error message.
        """
        app.logger.info(f'Update selection request received for selection id: {selection_id}')
        app.logger.debug(f'Request data: {data}')
        
        allowed_columns = list_diff(Selection().columns_list(), Selection()._restrict_in_update_)
        update_data = {}

        for column in allowed_columns:
            if column in data:
                update_data[column] = data.get(column)

        app.logger.debug(f'Selection data to be updated: {update_data}')

        result = Selection().validate_and_sanitize(update_data, Selection()._restrict_in_update_)
        if result.get("errors"):
            app.logger.error('Selection data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        if update_data:
            try:
                update_data["updated_at"] = datetime.utcnow()

                set_query = ', '.join([f"{column} = :{column}" for column in update_data.keys()])
                update_data["id"] = selection_id

                sql = f"""UPDATE selections SET {set_query} WHERE id = :id"""
                
                app.logger.info('Executing SQL query')
                operation_result = execute_sql_query(db, sql, update_data, operation="update")
                
                if not operation_result:
                    raise Exception('Failed to execute SQL query')

                db.session.commit()

                app.logger.info('Selection update successful')
                return {"message": f"Selection successfully updated with id={selection_id}"}
            except Exception as e:
                db.session.rollback()
                app.logger.error('Exception encountered during selection update')
                app.logger.debug(f'Exception details: {str(e)}')
                return {"error": str(e)}

        else:
            app.logger.info('No valid data found for update')
            return {"error": "No valid data found for update"}

    @staticmethod
    def delete_selection_permanently(selection_id):
        """
        Permanently delete a selection from the database.

        :param selection_id: [str] the id of the selection to delete.

        :return [dict]: Returns a dictionary containing a message of success or an error message.
        """
        app.logger.info(f'Delete selection request received for selection id: {selection_id}')

        try:
            sql = """DELETE FROM selections WHERE id = :id"""
            
            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, {"id": selection_id}, operation="delete")
            
            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Selection deletion successful')
            return {"message": f"Selection successfully deleted with id={selection_id}"}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during selection deletion')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}