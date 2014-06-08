import ConfigParser
import io

def get_config(config_file='config.rc'):
    '''Reads a config file and returns the instance.'''
    with open(config_file) as f:
        # Read values from config file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(f.read()))
    return config
