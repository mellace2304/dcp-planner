from Helper import * 

class Day_Interval:
    def __init__(self, code, day, start, end, semester, offering, taken, semester_taken_interval, num, model):
        self.code = code
        self.semester = semester
        self.offering = offering
        self.day = day
        self.start = time_to_int(start)
        self.end = time_to_int(end)
        self.duration = self.end - self.start
        self.taken = taken
        self.semester_taken_interval = semester_taken_interval
        self.interval = model.NewOptionalFixedSizeIntervalVar(self.start, self.duration, taken, f'{code}_{semester}_{day}_{start}_{num}')
    def summary(self):
        print(f'--Summary of {self.code} day interval--\nSemester: {self.semester}\nOffering: {self.offering}\nDay: {self.day}\nStart-End: {self.start} - {self.end}\n\n')  
