from Day_Interval import Day_Interval

class Option:
        def __init__(self, code, semester: int, semester_taken_interval, offering, day_and_times: dict, num:int, is_residential, model):
            self.semester = semester
            self.offering = offering
            self.num = num
            self.taken = model.NewBoolVar(f'{code}_{semester}_{num}')
            self.days_intervals = []
            self.day_times_dict = day_and_times
            self.code = code
            if day_and_times and offering in ['Residential','Both']:
                model.Add(self.taken == False).OnlyEnforceIf(is_residential.Not())
                for day, intervals in day_and_times.items():  
                    for interval_str in intervals.split(' | '):
                        start_time, end_time = interval_str.split(' - ')
                        NewInterval = Day_Interval(code,day,start_time,end_time,semester,offering,self.taken, semester_taken_interval, num, model)
                        self.days_intervals.append(NewInterval)
            else:
                model.Add(is_residential == False).OnlyEnforceIf(self.taken)
            
        def summary(self):
            print(f'Semester: {self.semester}\nDay and Times: {self.day_times_dict}\nCode: {self.code}\n\n')
