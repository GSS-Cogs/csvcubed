"""
Constants that are relevant to more than one qb component. 
"""

# A mapping of accepted datatypes from their csvw representation
# to appropriate primitive pandas dtypes.
# Please see:
# - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dtypes.html
# - https://numpy.org/doc/stable/reference/arrays.dtypes.html
ACCEPTED_DATATYPE_MAPPING = {
    "anyURI": "string",
    "boolean": "bool",
    "decimal": "float64",
    "integer": "int64",
    "long": "long",
    "int": "int64",
    "short": "short",
    "nonNegativeInteger": "uint64",
    "positiveInteger": "uint64",
    "unsignedLong": "uint64",
    "unsignedInt": "uint64",
    "unsignedShort": "uint64",
    "nonPositiveInteger": "int64",
    "negativeInteger": "int64",
    "double": "double",
    "float": "float64",
    "string": "string",
    "language": "string",
    "date": "string",
    "dateTime": "string",
    "dateTimeStamp": "string",
    "time": "string",
}