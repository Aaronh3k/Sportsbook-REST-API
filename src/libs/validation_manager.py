import pytz

import re
from datetime import datetime

class validationManager:

  @staticmethod
  def validate(data, assertions, skip=[], sanitize=True, join_msg=True):
    errors = []
    sanitized = {}
    required_keys = [k for k, v in assertions.items() if v["required"]]
    # remove all skip items from required keys
    required_keys = [x for x in required_keys if x not in skip]

    any_object_data_supplied = False
    for key, value in data.items():
      if sanitize and type(value) is str:
        #trim whitespace from string
        value = value.strip()
      sanitized[key] = value

      if key not in skip and assertions.get(key):
        any_object_data_supplied = True

        ## Start data type validation
        if assertions[key].get("type") == "string":
          errors.append(validationManager.string_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "enum":
          errors.append(validationManager.enum_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "boolean":
          errors.append(validationManager.boolean_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "integer":
          errors.append(validationManager.integer_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "date":
          errors.append(validationManager.date_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "datetime":
          errors.append(validationManager.datetime_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "float":
          errors.append(validationManager.float_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "array":
          errors.append(validationManager.array_validation(key, value, assertions.get(key)))
        elif assertions[key].get("type") == "time":
          errors.append(validationManager.time_validation(key, value, assertions.get(key)))
        else:
          errors.append("Invalid type for {}".format(key))

        if key in required_keys:
          required_keys.remove(key)

    if required_keys: # if there are some required filled not passed yet
      errors.append("Missing required fields: " + ", ".join(required_keys))

    # remove all None value from errors
    errors =  [i for i in errors if i]

    if join_msg:
      if not any_object_data_supplied:
        return {"errors": "No valid input data supplied", "data": sanitized}
      else:
        return {"errors": ", ".join(errors), "data": sanitized}
    else:
      if not any_object_data_supplied:
        return {"errors": ["No valid input data supplied"], "data": sanitized}
      else:
        return {"errors": errors, "data": sanitized}


  ### data type validations ###
  #############################

  @staticmethod
  def string_validation(key, value, assertion):
    if type(value) is str:
      if len(value) < assertion["min_length"] or len(value) > assertion["max_length"]:
        if not assertion["required"]:
          return "{}'s value is not required, but if supplied, then it must be min {} and max {} chars long".format(key, assertion["min_length"], assertion["max_length"])
        else:
          return '{} should be between {} and {} characters'.format(key, assertion["min_length"], assertion["max_length"])
      else:
        return None
    else:
      return "Invalid data type for {}. It's value {} is not a string".format(key, value)

  @staticmethod
  def enum_validation(key, value, assertion):
    if value not in assertion["options"]:
      if not assertion["required"]:
        return "{} is not required, but if supplied then it must be one of these {}".format(key, assertion["options"])
      else:
        return "{} must be one of these {}".format(key, assertion["options"])
    return None

  @staticmethod
  def boolean_validation(key, value, assertion):
    if type(value) is not bool:
      return "{} must be of data type boolean (true/false)".format(key)
    return None

  @staticmethod
  def integer_validation(key, value, assertion):
    if type(value) is int:
      if value < assertion["min_value"] or value > assertion["max_value"]:
        if not assertion["required"]:
          return "{}'s value is not required, but if supplied then, it's value  must be min {} and max {}".format(key, assertion["min_value"], assertion["max_value"])
        else:
          return "{} must be between {} to {} characters long".format(key, assertion["min_value"], assertion["max_value"])
      else:
        return None
    else:
      return "Invalid data type for {}. Supplied data is not an integer".format(key)

  @staticmethod
  def float_validation(key, value, assertion):
    if type(value) is float:
      if value < assertion["min_value"] or value > assertion["max_value"]:
        if not assertion["required"]:
          return "{}'s value is not required, but if supplied then it's value i.e. {} must be min {} and max {}".format(key, value, assertion["min_value"], assertion["max_value"])
        else:
          return "{} must be between {} to {} characters long".format(key, assertion["min_value"], assertion["max_value"])
      else:
        return None
    else:
      return "Invalid data type for {}. Supplied value is not a float".format(key)

  @staticmethod
  def date_validation(key, value, assertion):
    try:
      if value != datetime.strptime(value, "%Y-%m-%d").strftime('%Y-%m-%d'):
        raise ValueError
      return None
    except ValueError:
      return "{} value is of incorrect data format, should be YYYY-MM-DD".format(value)

  @staticmethod
  def datetime_validation(key, value, assertion):
    try:
      if value != datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S'):
        raise ValueError
      return None
    except ValueError:
      return "{} value is of incorrect datatime format, should be YYYY-MM-DD HH:MM:SS".format(value)

  @staticmethod
  def array_validation(key, value, assertion):
    if type(value) is list:
      if len(value) < assertion["min_length"] or len(value) > assertion["max_length"]:
        if not assertion["required"]:
          return "{}'s value is not required, but if supplied then, it's length must be min {} and max {}".format(key, assertion["min_length"], assertion["max_length"])
        else:
          return "{}'s length must be min {} and max {}".format(key, assertion["min_length"], assertion["max_length"])
      elif assertion["options"] and not all(val in assertion["options"] for val in value):
        if not assertion["required"]:
          return "{} is not required, but if supplied then it must be one of these {}".format(key, assertion["options"])
        else:
          return "{} must be one of these {}".format(key, assertion["options"])
      else:
        return None
    else:
      return "Invalid data type for {}. Supplied data is not an list".format(key)

  @staticmethod
  def time_validation(key, value, assertion):
    try:
      if '1900-01-01T' in value:
        return None
      if value != datetime.strptime(value, "%H:%M:%S").strftime("%H:%M:%S"):
        raise ValueError
      return None
    except ValueError:
      return "{} value is of incorrect time format, should be HH:MM:SS".format(value)