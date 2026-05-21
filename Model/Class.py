from Node import Node
from Option import Option
import pandas as pd
import re

class Class:
    def __init__(self, code, title, credits, residential_prereqs, online_prereqs, offerings, additional, model, semester_domain):
        self.model = model
        if '-' in credits:
            self.credits = int(credits.split('-')[1])
        elif ',' in credits:
            self.credits = int(credits.split(',')[1])
        else:
            self.credits = int(credits)
        self.code = code
        self.title = title
        self.resid_prereq = residential_prereqs
        self.online_prereq = online_prereqs
        if isinstance(online_prereqs,float):
            self.online_prereq = residential_prereqs
        else:
            self.online_prereq = online_prereqs

        self.str_prereqs = {}
        
        self.additional = additional
        self.prereq_enforced = self.model.NewBoolVar(f'{self.code}_prereq_enforced')
        self.is_present = self.model.NewBoolVar(f'{self.code}_is_present')
        self.is_residential = self.model.NewBoolVar(f'{self.code}_offering')
        self.semester_taken = self.model.NewIntVarFromDomain(semester_domain, f'{self.code}_semester')
        self.semester_taken_interval = self.model.NewFixedSizeIntervalVar(self.semester_taken*100,1,f'{self.code}_semester_taken')

        self.is_fall = self.model.NewBoolVar(f'{code}_is_fall')
        q = self.model.NewIntVar(0, 5, f'q_{self.code}')  
        r = self.model.NewIntVar(0, 1, f'r_{self.code}')
        self.model.Add(self.semester_taken == 2 * q + r)
        
        self.model.Add(r == 1).OnlyEnforceIf(self.is_fall)
        self.model.Add(r == 0).OnlyEnforceIf(self.is_fall.Not())

        if offerings == 'Residential':
            self.offering = 'Residential'
            self.model.Add(self.is_residential == True)
        elif offerings == 'Online':
            self.offering = 'Online'
            self.model.Add(self.is_residential == False)
        else:
            self.offering = 'Both'

        self.transferred = self.model.NewBoolVar(f'{self.code}_transferred')
        
        self.model.Add(self.is_present == False).OnlyEnforceIf(self.transferred)

        self.completed = self.model.NewBoolVar(f'{self.code}_completed')

        self.model.AddBoolOr([self.transferred,self.is_present]).OnlyEnforceIf(self.completed)
        self.model.AddBoolAnd([self.transferred.Not(),self.is_present.Not()]).OnlyEnforceIf(self.completed.Not())
        self.options = []

    def add_meeting_times(self, class_offerings_df: pd.DataFrame):
        seen_intervals = []
        for index, class_offering in class_offerings_df.iterrows(): 
            semester = class_offering['Semester'].split()[0]
            
                
            if class_offering['Location'] != 'Online' and len(class_offering['Time'].split(' | ')) != 1:
                unique_str = class_offering['Time']+semester
                if unique_str in seen_intervals:
                    continue
                times_dict = {}
                for times in class_offering['Time'].split(' and '):
                    time_interval = times.split(' | ')[1]
                    for day in times.split(' | ')[0].split():
                        if times_dict.get('day'):
                            
                            times_dict[day] = times_dict[day] + f' | {time_interval}'
                        else:
                            times_dict[day] = time_interval
                option = Option(code = self.code,semester = semester, semester_taken_interval=self.semester_taken_interval, offering = 'Residential', day_and_times = times_dict, num = index, is_residential = self.is_residential,model= self.model)
                self.options.append(option)
                seen_intervals.append(unique_str)
            else:
                unique_str = 'Online '+semester
                if unique_str in seen_intervals:
                    continue
                option = Option(code = self.code, semester = semester, semester_taken_interval=self.semester_taken_interval, offering = 'Online', day_and_times={}, num = index, is_residential = self.is_residential,model = self.model)
                self.options.append(option)
                seen_intervals.append(unique_str)   
           
            
        #some option has to be taken if a class is taken
        if len([option.taken for option in self.options]) != 0:
            self.model.Add(sum([option.taken for option in self.options]) == 1).OnlyEnforceIf(self.is_present)
            self.model.Add(sum([option.taken for option in self.options]) == 0).OnlyEnforceIf(self.is_present.Not())
            #if taken in the fall or spring, fall semesters are odd
            fall_options = [option.taken for option in self.options if option.semester == 'Fall']
            spring_options = [option.taken for option in self.options if option.semester == 'Spring']
            self.model.Add(sum(fall_options) == 0).OnlyEnforceIf([self.is_fall.Not(), self.is_present])
            self.model.Add(sum(spring_options) == 0).OnlyEnforceIf([self.is_fall,self.is_present])
        else:
            self.model.Add(self.is_present == False)
    
    def add_prerequisites(self, semester_map: dict,completed_credits,All_Classes,additional_completions):
        def parse_acceptably(string: str):
            
            token_pattern = re.compile(r"""
                (\()                                      # Group 1: Opening parenthesis
            |   (\))                                      # Group 2: Closing parenthesis
            |   (\[[^\[\]]+\]\{[^{}]+\})                  # Group 3: [Course]{modifier}
            |   (\[[^\[\]]+\])                            # Group 4: [Course]
            |   (\band\b|\bor\b|\bnot\b)                  # Group 5: Logical operators
            |   ([^()\[\]\s]+(?:\s(?!and\b|or\b|not\b)[^()\[\]\s]+)*)   # Group 6: Other phrases
            """, re.IGNORECASE | re.VERBOSE)

            matches = token_pattern.findall(string)

            # Flatten and strip non-empty matches
            tokens = [token.strip() for group in matches for token in group if token]

            output = []
            stack = []
            precedence = {
                'and': (2, 'left'),
                'or':  (1, 'left'),
            }
            for token in tokens:
                if token == '(':
                    stack.append(token)
                elif token == ')':
                    while stack and stack[-1] != '(':
                        output.append(stack.pop())
                    stack.pop()
                elif token in ['and', 'or']:
                    while (stack and stack[-1] in ['and', 'or']) and (precedence[token][0] <= precedence[stack[-1]][0]):
                        output.append(stack.pop())
                    stack.append(token)
                else:
                    output.append(token)
            while stack:
                output.append(stack.pop())
            cleaned_tokens = output
            return cleaned_tokens

        def build_ast(tokens):
            stack = []
            for token in tokens:
                if token in ['and', 'or']:
                    right = stack.pop()
                    left = stack.pop()
                    node = Node(token, left, right, self.code, semester_map, self.semester_taken, completed_credits, All_Classes, additional_completions,self.model)
                    stack.append(node)
                else:
                    stack.append(Node(token, None, None, self.code, semester_map, self.semester_taken, completed_credits, All_Classes, additional_completions,self.model))
            return stack[0]
        
        if not isinstance(self.resid_prereq, float):    
            resid_tokens = parse_acceptably(self.resid_prereq)
            self.resid_prereq_tree = build_ast(resid_tokens)
            self.resid_prereq_enforced = self.resid_prereq_tree.var
            
            self.model.Add(self.resid_prereq_enforced == True).OnlyEnforceIf([self.is_present,self.is_residential])
        else:
            self.resid_prereq_enforced = self.model.NewBoolVar(f'{self.code}_resid_prereq_enforced')


        if not isinstance(self.online_prereq,float):
            online_tokens = parse_acceptably(self.online_prereq)
            self.online_prereq_tree = build_ast(online_tokens)
            self.online_prereq_enforced = self.online_prereq_tree.var

            self.model.Add(self.online_prereq_enforced == True).OnlyEnforceIf([self.is_present,self.is_residential.Not()]) 
        else:
            self.online_prereq_enforced = self.model.NewBoolVar(f'{self.code}_online_prereq_enforced')
        
        self.model.AddBoolOr([self.resid_prereq_enforced,self.online_prereq_enforced]).OnlyEnforceIf(self.prereq_enforced)
        self.model.AddBoolAnd([self.resid_prereq_enforced.Not(),self.online_prereq_enforced.Not()]).OnlyEnforceIf(self.prereq_enforced.Not())
    def __getitem__(self,key):
        match key:
            case 'code':
                return self.code
            case 'title':
                return self.title
            case 'completed':
                return self.completed
            case 'credits':
                return self.credits
            case 'is_fall':
                return self.is_fall
            case 'semester_taken':
                return self.semester_taken
