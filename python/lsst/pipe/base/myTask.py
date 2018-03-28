from .task import Task
from lsst.pex.config import Config
class MyTask(Task):
    _DefaultName = 'MyTask'
    ConfigClass = Config
    def run(self):
        print("This method runs stuff...")
