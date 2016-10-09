from api.api import server_accessor

api_server = server_accessor('http://enron.cs.northwestern.edu/~madhav/treftun/mta/api/', username='root', password='password')

date_fmt = '%Y-%m-%d %H:%M:%S'
dictLogConfig = {
    "version":1,
    "handlers":{
        "fileHandler":{
            "class":"logging.FileHandler",
            "formatter":"myFormatter",
            "filename":"mta.log"
        }
    },
    "loggers":{
        "mtalib":{
            "handlers":["fileHandler"],
            "level":"DEBUG",
        }
    },

    "formatters":{
        "myFormatter":{
            "format":"%(asctime)s - %(name)s - [%(pathname)s:%(lineno)d] - %(levelname)s - %(message)s"
        }
    }
}
