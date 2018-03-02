from .task import Task
from lsst.pex.config import Config
class MyTask(Task):
    _DefaultName = 'MyTask'
    ConfigClass = Config
    def run(self):
        print("This method runs stuff...")

    def run2(self):
        self.run()
        print("This method runs stuff 2...")
