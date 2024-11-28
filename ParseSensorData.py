
def getLatestMeasurement(data):
    """ Returns latest measurement information

        Parameters:
        - Expects data dictionary
    """
    latest_measurement = data['data']['connection']['glucoseMeasurement']['Value']
    return latest_measurement

def getLatestMeasurementTimestamp(data):
    """ Returns TS for latest measurement information

        Parameters:
        - Expects data dictionary
    """
    latest_measurement_ts = data['data']['connection']['glucoseMeasurement']['Timestamp']
    return latest_measurement_ts


def getLatestMeasurementTrendArrow(data):
    """ Returns TS for latest measurement trend information
        3: Flat

        Parameters:
        - Expects data dictionary
    """
    latest_measurement_ta = data['data']['connection']['glucoseMeasurement']['TrendArrow']
    return latest_measurement_ta












def getAllMeasurements(data):
    """ Returns all measurements with information

        Parameters:
        - Expects data dictionary
    """
    all_measurements = data['data']['graphData']
    return all_measurements
