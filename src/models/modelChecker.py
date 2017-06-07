# This is the model checker that checks if the model implementation fits the
# requirement.
import os
import sys
import inspect
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from loggers import logging, init_logger

supportedModels = [
    "IBM1Old", "IBM1New"
]


def checkAlignmentModel(modelClass):
    logger = logging.getLogger('CheckModel')
    if not inspect.isclass(modelClass):
        logger.error(
            "Specified Model needs to be a class named AlignmentModel under " +
            "models/ModelName.py")
        return False

    trainMethod = getattr(modelClass, "train", None)
    if not callable(trainMethod):
        logger.error(
            "Specified Model class needs to have a method called train, " +
            "containing at least the following arguments: " +
            "biText(list of (str, str)), iterations(int)")
        return False

    decodeToFileMethod = getattr(modelClass, "decodeToFile", None)
    if not callable(decodeToFileMethod):
        logger.error(
            "Specified Model class needs to have a method called " +
            "decodeToFileMethod, containing at least the following " +
            "arguments: biText(list of (str, str)), iterations(int)")
        return False
    return True

if __name__ == '__main__':
    init_logger("UTmodels.log")
    print "Launching unit test on: models.modelChecker.checkAlignmentModel"
    print "This test will test the behaviour of checkAlignmentModel on all",\
        "supported models:\n", supportedModels

    import importlib
    for name in supportedModels:
        Model = importlib.import_module("models." + name).AlignmentModel
        if checkAlignmentModel(Model):
            print "Model", name, ": passed"
        else:
            print "Model", name, ": failed"
