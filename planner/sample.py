from copy import deepcopy

SAMPLE = {
    'name': 'New Delhi · sample route',
    'start': {'name': 'Sample depot · Connaught Place', 'address': 'Connaught Place, New Delhi, Delhi, India', 'lat': 28.6315, 'lng': 77.2167, 'notes': 'Illustrative starting point near the landmark, not a real depot.'},
    'stops': [
        {'name': 'Sample stop · Khan Market', 'address': 'Khan Market, New Delhi, Delhi, India', 'lat': 28.6004, 'lng': 77.2270, 'notes': 'Fictional parcel delivery near the market. Confirm the shop and entrance before travel.'},
        {'name': 'Sample stop · Gole Market', 'address': 'Gole Market, New Delhi, Delhi, India', 'lat': 28.6337, 'lng': 77.2057, 'notes': 'Fictional kirana delivery near the market. Add the shop number to a real order.'},
        {'name': 'Sample stop · Mandi House', 'address': 'Mandi House, New Delhi, Delhi, India', 'lat': 28.6259, 'lng': 77.2343, 'notes': 'Fictional office delivery near the landmark. Check building access before arrival.'},
        {'name': 'Sample stop · India Gate', 'address': 'India Gate, New Delhi, Delhi, India', 'lat': 28.6129, 'lng': 77.2295, 'notes': 'Public landmark for demonstration only. Not a delivery address; check road access restrictions.'},
    ],
    'return_to_start': True, 'mode': 'demo',
}


def sample_route():
    return deepcopy(SAMPLE)
