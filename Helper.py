def time_to_int(time: str):
    hours, stuff = time.split(':')
    minutes, type = stuff.split()
    time_min = int(minutes)
    
    if type.lower() == 'pm' and int(hours) != 12:
        time_min += (int(hours) + 12) * 60
    elif type.lower() == 'am' and int(hours) == 12:
        time_min += 0  # 12 AM is midnight
    else:
        time_min += int(hours) * 60
    
    return time_min

def int_to_semester(num:int):
    dict = {1:'Freshman Fall',
            2:'Freshman Spring',
            3:'Sophomore Fall',
            4:'Sophomore Spring',
            5:'Junior Fall',
            6:'Junior Spring',
            7:'Senior Fall',
            8:'Senior Spring'
            }
    return dict[num]

def int_to_time(num:int):
    q, r = divmod(num, 60)
    if q == 24:
        return f'{q:02}:{r:02} AM'
    elif q > 12:
        q-=12
        return f'{q:02}:{r:02} PM'
    elif q == 0:
        return f'{q+12:02}:{r:02} AM'
    else:
        return f'{q:02}:{r:02} AM'
