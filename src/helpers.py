import ujson
from flask import Response
from src.config.config import *
from sqlalchemy import text

def responsify(payload, links={}, http_code=200, mimetype="application/json"):
  """
  An utility for returning reponse of an api call

  :param  payload: [dictionary] e.g. {"name": "john"}
  :param  links: [dictionary] e.g. {"movie_url": "http://sdsd.com/232/movie.html"}
  :param  http_code: [integer]
  :param  mimetype: [string]

  :return [Object] Response object
  """
  if links:
    payload = payload or {}  # If payload is None, initialize it as an empty dict
    payload["links"] = links

  data = ujson.dumps(payload) if payload else None

  return Response(response=data, status=http_code, mimetype=mimetype)
  
  
def errorit(msg, custom_code, http_code=400, info="", mimetype="application/json", debug_info=None, **kwargs):
  """
  An utility for returning error reponse of an api call

  :param  msg: [string or array] e.g. "user not found"
  :param  custom_code: [string] e.g. USER_NOT_FOUND
  :param  http_code: [integer]
  :param  info: [string] e.g. For more info visit xyz.com/eww
  :param  mimetype: [integer]
  :param  debug_info: [dictionary] - any data to be returned
  :param kwargs: [dictionary] - custom data
  :return [Object] Response object
  """
  return Response(
    response=err_dict(msg, custom_code, ( "{}{}".format(API_URI, info) if info else ""), debug_info, **kwargs),
    status=http_code,
    mimetype=mimetype
  )

def err_dict(msg, code, info="", debug_info=None, **kwargs):
  """
  An utility for building error json

  :param  msg: [array] e.g. "user not found"
  :param  code: [string] e.g. USER_NOT_FOUND
  :param  info: [string] e.g. For more info visit xyz.com/eww
  :param  debug_info: [dictionary] - any data to be returned

  :return [String] json
  """  
  if not isinstance(msg, list): # convert message to an array, if it is not
    msg = [msg]

  dc = {
    "errors": msg,
    "code": code,
    **kwargs
  }

  if not code:
    dc.pop("code")
  if info:
    dc.update({"info": info})
  if debug_info:
    dc.update({"debug_info": debug_info})

  dc["service"] = SERVICE_ID

  return ujson.dumps(dc)

def list_diff(l1, l2):
  """
  Find differnce between two lists
  """
  return [i for i in l1 + l2 if i not in l1 or i not in l2]

def datetime_to_str(dt, with_time=False, no_day=False):
  """
  Convert datetime to string YY-MM-DD format

  :param  d: [object] - datetiem object

  :return [string] - YYYY-MM-DD string
  """
  try:
    if no_day:
      return dt.strftime("%Y-%m") if not with_time else dt.strftime("%Y-%mT%H:%M:%SZ")
    else:
      return dt.strftime("%Y-%m-%d") if not with_time else dt.strftime("%Y-%m-%dT%H:%M:%SZ")
  except:
    return None

def execute_sql_query(db, sql_query, params=None, operation="select", fetchone=False):
    """
    Executes a SQL query and returns the results.
    :param sql_query: [str] SQL query to execute
    :param params: [dict] Parameters to substitute into the SQL query
    :param operation: [str] The type of SQL operation being performed: "select", "insert", "update", "delete"
    :return: [ResultProxy / None] Result of the SQL query, if any
    """
    try:
        result = db.session.execute(text(sql_query), params) if params else db.session.execute(text(sql_query))
        if operation.lower() == "select":
            if fetchone:
              return result.fetchone()
            return result.fetchall()
        
        elif operation.lower() in ["insert", "update", "delete"]:
            db.session.flush()
            return True
        
        else:
            raise ValueError(f"Unsupported SQL operation: {operation}")

    except Exception as e:
        return None

