incorrectState =0
phase = 0
reps = 0
incorrect_reps
def count(percent,isCorrect = False):
    if(not iscorrect):
        incorrectState = 1
    if(percent == 100):
        if phase == 0:
            phase = 1
    if percent == 0:
        if phase == 1:
            if(incorrectState == 1):
                incorrect_reps +=1
            else:
                reps+=1    

            phase = 0
            incorrectState = 0 
    return reps,incorrect_reps           
