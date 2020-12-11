import csv


class CSVReader:
    def __init__(self, pathToFile):
        self.file_path = pathToFile

    def read(self):
        with open(self.file_path) as answerList:
            reader = csv.DictReader(answerList, delimiter=',')
            return list(reader)