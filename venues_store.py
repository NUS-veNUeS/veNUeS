'''
A database storing the venues information.
venues {
  room: {
    lat: float,
    long: float,
    location: str,
    availability: dict
  },
}
'''
VENUES_LIST = []

VENUES = {}

LOCATIONS = {
    'BIZ': [],
    'ENGIN': [],
    'FASS': [],
    'FOS': [],
    'I3': [],
    'LAW': [],
    'SDE': [],
    'SOC': [],
    'UTOWN': [],
    'YALE': [],
    'YLLSM': [],
    'YSTCM': []
}

LOCATIONKEYS = ['BIZ📈',
    'ENGIN⚙️',
    'FASS🎭',
    'FOS🧪',
    'I3💡',
    'LAW⚖️',
    'SDE🏛',
    'SOC🖥',
    'UTOWN📚',
    'YALE🐦',
    'YLLSM🩺',
    'YSTCM🎼']
