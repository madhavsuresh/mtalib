import config
import logging
import logging.config
import events.event as event
import api.api

def main():
    logging.config.dictConfig(config.dictLogConfig)
    logger = logging.getLogger('mtalib')
    try:
        e = event.EventAssignment(2, config.api_server)
        e.execute_state()
    except:
        logger.exception('run.py failed')

if __name__ == '__main__':
    main()
