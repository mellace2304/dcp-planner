
class Node:
    def __init__(self, value: str, left, right, code, semester_map: dict,self_semester_taken,completed_credits,All_Classes,additional_completions,model):
        self.value = value
        self.left = left
        self.right = right
        self.code = code
        
        if value == 'or':
            self.var = model.NewBoolVar(f'or_{left.value}_{right.value}_for_{code}')
            model.AddBoolOr([left.var,right.var]).OnlyEnforceIf(self.var)
            model.AddBoolAnd([left.var.Not(),right.var.Not()]).OnlyEnforceIf(self.var.Not())
        elif value == 'and':
            self.var = model.NewBoolVar(f'and_{left.value}_{right.value}_for_{code}')
            model.AddBoolAnd([left.var,right.var]).OnlyEnforceIf(self.var)
            model.AddBoolOr([left.var.Not(),right.var.Not()]).OnlyEnforceIf(self.var.Not())
        else:
            self.var = model.NewBoolVar(f'{value}_for_{code}')
            prereq_code = value.split(']{')[0].replace('[','').replace(']','')
            if prereq_code in completed_credits:
                model.Add(self.var == True)
            elif prereq_code in semester_map.keys():
                prereq_semester_taken = semester_map[prereq_code][0]
                prereq_is_present = semester_map[prereq_code][1]
                prereq_prereq_enforced = semester_map[prereq_code][2]
                
                if 'concurrent' in value:
                    concurrent_semester_check = model.NewBoolVar(f'Concurrent_Or_Less_Semester_{prereq_code}_{self.code}')

                    model.Add(prereq_semester_taken <= self_semester_taken).OnlyEnforceIf(concurrent_semester_check)
                    model.Add(prereq_semester_taken > self_semester_taken).OnlyEnforceIf(concurrent_semester_check.Not())
                    
                    model.AddBoolAnd([prereq_is_present,concurrent_semester_check,prereq_prereq_enforced]).OnlyEnforceIf(self.var)
                    model.AddBoolOr([prereq_is_present.Not(),concurrent_semester_check.Not(),prereq_prereq_enforced.Not()]).OnlyEnforceIf(self.var.Not())

                else:
                    nonconcurrent_semester_check = model.NewBoolVar(f'NonConcurrent_Or_Less_Semester_{prereq_code}_{self.code}')

                    model.Add(prereq_semester_taken < self_semester_taken).OnlyEnforceIf(nonconcurrent_semester_check)
                    model.Add(prereq_semester_taken >= self_semester_taken).OnlyEnforceIf(nonconcurrent_semester_check.Not())

                    model.AddBoolAnd([prereq_is_present,nonconcurrent_semester_check]).OnlyEnforceIf(self.var)
                    model.AddBoolOr([prereq_is_present.Not(),nonconcurrent_semester_check.Not()]).OnlyEnforceIf(self.var.Not())
            else:
                All_Classes[self.code].str_prereqs[self.value] = self.var
                if self.value in additional_completions:
                    model.Add(self.var == True)
                else:
                    model.Add(self.var == False)