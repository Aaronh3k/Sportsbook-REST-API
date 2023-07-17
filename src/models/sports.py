from datetime import datetime
from src.app import db, app
import uuid
from src.models.mixins import BaseMixin
from src.helpers import *
from sqlalchemy import exc, text

class Sport(BaseMixin, db.Model):
    __tablename__ = "sports"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    url_identifier = db.Column(db.String(255), nullable=False, unique=True)
    active = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    _validations_ = {
        "name": {"type": "string", "required": True, "min_length": 1, "max_length": 255},
        "url_identifier": {"type": "string", "required": True, "min_length": 1, "max_length": 255}
    }

    _restrict_in_creation_  = ["id", "active", "created_at", "updated_at"]
    _restrict_in_update_    = ["id", "active", "created_at", "updated_at"]
    
    @staticmethod
    def create_a_sport(data):
        """
        Create a new sport
        :param data: [object] contains sport info in key value pair

        :return [dict]
        """
        app.logger.info('Sport creation initiated')

        allowed_columns = list_diff(Sport().columns_list(), Sport()._restrict_in_creation_)
        insert_data = {}

        for column in allowed_columns:
            if column in data:
                insert_data[column] = data.get(column)

        app.logger.debug(f'Sport data to be inserted: {insert_data}')
        
        result = Sport().validate_and_sanitize(insert_data, Sport()._restrict_in_creation_)
        if result.get("errors"):
            app.logger.error('Sport data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        try:
            sql = """INSERT INTO sports({}) VALUES ({})""".format(
                ', '.join(insert_data.keys()),
                ', '.join([':' + k for k in insert_data.keys()])
            )

            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, insert_data, operation="insert")
           
            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Sport creation successful')
            return {"message": "Sport successfully created"}
        except exc.IntegrityError as e:
            db.session.rollback()
            err = e.orig.diag.message_detail.rsplit(',', 1)[-1]
            app.logger.error('SQL integrity error encountered')
            app.logger.debug(f'Error details: {err.replace(")", "")}')
            return {"error": err.replace(")", "")}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during sport creation')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}

    @staticmethod
    def get_sports(sport_id=None, page=None, offset=None, orderby=None, sortby=None, active=None):
        """
        Get sports data by sport_id or get paginated list of sports

        :param sport_id: [str] sports table primary key
        :param page: [int] page number
        :param offset: [int] page offset - number of rows to return
        :param orderby: [int] sort order (-1 for descending, 1 for ascending)
        :param sortby: [str] column to sort by
        :param active: [bool] active state of the sport

        :return [dict/list]
        """
        page = page or 1
        offset = offset or 20
        orderby = orderby or "ASC"
        sortby = sortby or "name"
        active_query = ""

        if active is not None:
            active = bool(active)
            active_query = f"WHERE active = {active}"

        app.logger.info('Sport retrieval request received')
        app.logger.debug(f'Request parameters - sport_id: {sport_id}, page: {page}, offset: {offset}, orderby: {orderby}, sortby: {sortby}, active: {active}')

        try:
            if not sport_id:
                offset = int(offset)
                page = int(page) - 1
                sql = f"SELECT * FROM sports {active_query} ORDER BY {sortby} {orderby} LIMIT {offset} OFFSET {page * offset}"
                sports = execute_sql_query(db, sql, operation="select")
                
                if not sports:
                    return {"sports": [], "meta_data": {"sport_count": 0, "page_number": page + 1, "page_offset": offset}}

                sports_dict = []
                for sport in sports:
                    created_at = datetime_to_str(sport[4], True) if sport[4] else None
                    updated_at = datetime_to_str(sport[5], True) if sport[5] else None

                    sport_dict = dict(zip(("id", "name", "url_identifier", "active", "created_at", "updated_at"), 
                        (sport[0], sport[1], sport[2], sport[3], created_at, updated_at)))

                    sport_dict = {k: v for k, v in sport_dict.items() if v is not None}
                    
                    sports_dict.append(sport_dict)

                count_sql = f"SELECT COUNT(*) FROM sports {active_query}"
                total_sports = execute_sql_query(db, count_sql, operation="select")
                total_sports = total_sports[0][0] if total_sports else 0

                app.logger.info(f'Retrieved {total_sports} sports')

                return {"sports": sports_dict, "meta_data": {"sport_count": total_sports, "page_number": page + 1, "page_offset": offset}}

            else:
                sql = f"SELECT * FROM sports WHERE id = :id"
                sport = execute_sql_query(db, sql, {"id": sport_id}, operation="select", fetchone=True)

                if not sport:
                    return None
                

                created_at = datetime_to_str(sport[4], True) if sport[4] else None
                updated_at = datetime_to_str(sport[5], True) if sport[5] else None

                sport_dict = dict(zip(("id", "name", "url_identifier", "active", "created_at", "updated_at"), 
                    (sport[0], sport[1], sport[2], sport[3], created_at, updated_at)))

                sport_dict = {k: v for k, v in sport_dict.items() if v is not None}

                app.logger.info(f'Retrieved sport with id {sport_id}')

                return sport_dict

        except Exception as e:
            app.logger.error('Sport retrieval failed')
            app.logger.debug(f'Error details: {e}, sport_id: {sport_id}, page: {page}, offset: {offset}')
            return None

    @staticmethod
    def update_a_sport(sport_id, data):
        """
        Update an existing sport

        :param sport_id: [str] sports table primary key
        :param data: [dict] sport updating field data

        :return [dict]
        """
        app.logger.info(f'Update sport request received for sport id: {sport_id}')
        app.logger.debug(f'Request data: {data}')
        
        allowed_columns = list_diff(Sport().columns_list(), Sport()._restrict_in_update_)
        update_data = {}

        for column in allowed_columns:
            if column in data:
                update_data[column] = data.get(column)

        app.logger.debug(f'Sport data to be updated: {update_data}')

        result = Sport().validate_and_sanitize(update_data, Sport()._restrict_in_update_)
        if result.get("errors"):
            app.logger.error('Sport data validation and sanitization failed')
            app.logger.debug(f'Validation errors: {result["errors"]}')
            return {"error": result["errors"]}

        if update_data:
            try:
                update_data["updated_at"] = datetime.utcnow()

                set_query = ', '.join([f"{column} = :{column}" for column in update_data.keys()])
                update_data["id"] = sport_id

                sql = f"""UPDATE sports SET {set_query} WHERE id = :id"""
                
                app.logger.info('Executing SQL query')
                operation_result = execute_sql_query(db, sql, update_data, operation="update")
                
                if not operation_result:
                    raise Exception('Failed to execute SQL query')

                db.session.commit()

                app.logger.info('Sport update successful')
                return {"message": f"Sport successfully updated with id={sport_id}"}
            except Exception as e:
                db.session.rollback()
                app.logger.error('Exception encountered during sport update')
                app.logger.debug(f'Exception details: {str(e)}')
                return {"error": str(e)}
        else:
            app.logger.info('No valid update fields provided')
            return {"error": "No valid update fields provided"}

    @staticmethod
    def delete_sport_permanently(sport_id):
        """
        Delete an existing sport permanently

        :param sport_id: [str] sports table primary key

        :return [dict]
        """
        app.logger.info(f'Delete sport request received for sport id: {sport_id}')

        try:
            sql = """DELETE FROM sports WHERE id = :id"""
            params = {"id": sport_id}
            
            app.logger.info('Executing SQL query')
            operation_result = execute_sql_query(db, sql, params, operation="delete")

            if not operation_result:
                raise Exception('Failed to execute SQL query')

            db.session.commit()

            app.logger.info('Sport deletion successful')
            return {"message": f"Sport successfully deleted with id={sport_id}"}
        except Exception as e:
            db.session.rollback()
            app.logger.error('Exception encountered during sport deletion')
            app.logger.debug(f'Exception details: {str(e)}')
            return {"error": str(e)}

