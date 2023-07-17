"""
Mixins for model classes: BaseMixin
"""

import datetime

from sqlalchemy.orm import class_mapper, ColumnProperty
from src.helpers import *
from src.libs.validation_manager import validationManager

class BaseMixin(object):

  def validate_and_sanitize(self, data, skip=[]):
    if not hasattr(self, "_validations_"):
      return {}

    try:
      result = validationManager.validate(data, self._validations_, skip, True)
      if not result["errors"]:
        for  k, v in result.get("data").items():
          # reset the value with sanitized data
          setattr(self, k, v)
          return {}
      else:
        return {"errors": result["errors"]}
    except Exception as e:
      return {"errors": ["Data validation failed"]}


#   def to_dict(self, ts_to_string = True, dt_to_string= True, remove_null=True, hide_fields=[]):
#     """
#     return model as python dictionary

#     :param ts_to_string: [bool] convert timestamp to YYYY-MM-DD string
#     :param dt_to_string: [bool] convert datetime object to "2016-10-21T23:46:50Z" format
#     :param remove_null: [bool] remove key=>value pair, where value is empty

#     :return [dict] cleaned dictionary of the model
#     """
#     result = {}

#     for prop in class_mapper(self.__class__).iterate_properties:
#       if isinstance(prop, ColumnProperty):
#         value = getattr(self, prop.key)
#         if remove_null:
#           if getattr(self, prop.key) == None:
#             continue

#         if ts_to_string and value and prop.key in ["start", "end"]:
#           value = timestamp_to_string(value)

#         if dt_to_string and value and (isinstance(value, datetime.datetime) or isinstance(value, datetime.time)):
#           value = datetime_to_str(value, True)

#         if dt_to_string and value and (isinstance(value, datetime.date)):
#           value = datetime_to_str(value, False)

#         if dt_to_string and value and prop.key in ["dates"] and isinstance(value, list):
#           value = [datetime_to_str(dates, False, True) for dates in value]

#         if prop.key not in hide_fields:
#           result[prop.key] = value

#     return result

  def columns_list(self):
    columns = []
    for prop in class_mapper(self.__class__).iterate_properties:
      if isinstance(prop, ColumnProperty):
        columns.append(prop.key)

    return columns
