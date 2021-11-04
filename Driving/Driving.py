
import StimToolLib, os, random, operator, math, copy
from psychopy import visual, core, event, data, gui, sound
from fractions import Fraction #to make definition of probability distributions more intuitive
from psychopy.hardware import joystick

#Change Point Detection task

class GlobalVars:
    #This class will contain all module specific global variables
    #This way, all of the variables that need to be accessed in several functions don't need to be passed in as parameters
    #It also avoids needing to declare every global variable global at the beginning of every function that wants to use it
    def __init__(self):
        self.win = None #the window where everything is drawn
        self.clock = None #global clock used for timing
        self.x = None #X fixation stimulus
        self.output = None #The output file
        self.msg = None
        self.timer_msg = None #message used for countdown timer
        self.ideal_trial_start = None #ideal time the current trial started
        self.this_trial_output = '' #will contain the text output to print for the current trial
        self.instructions = []
        #self.dot_locations = [(-2.12, 2.12), (-.78,-2.90), (2.90, .78)]#[(-212, 212), (-78,-290), (290, 78)]
        #self.dots = [] #dot patches
        #self.circles_white = [] #white circles that go over dot patches when they're not being displayed
        #self.circles_red = [] #red circles used to illuminate correct response (when incorrect response is given)
        #self.circles_green = [] #green circles used to show correct response
        self.bar_red = None
        self.bar_green = None #red and green point bars
        self.bar_x = -350 #x location of time bar (should be just left of stop line)
        self.bar_width = 50 #width of the time bar
        self.trial = None #trial number
        self.trial_type = None #current trial type
        self.break_instructions = ['''You may now take a short break.''']
        self.block_points = 0 #points earned this block
        self.total_points = 0 #total points earned so far
        self.block_correct = 0 #number of correct responses in this block
        self.direction_text = None #will be right or left
        self.car = None #car stimulus
        self.joy = None #joystick object
        self.car_start_pos = [0, -8] #starting position for the car (in cm, both trial types)
        self.target = None #white circle used in move/go trials
        self.sound_beep1 = None #beeps for countdown timers
        self.sound_beep2 = None
        self.A = -0.35 #equilibrium point--makes it so the subject has to continue holding the stick forward just a little to remain stopped at the line
        self.B = 15.0 #maximum speed in cm/s
        self.C = 2  # 0 is very ICY, 2, is not so ICY, start at 2
        self.dy = 0.0
        self.stick_move_threshold = 0.03 #threshold used to determine when the subject has responded on move-go trials, to flag false starts, and to start speed-and-stop trials
        self.move_go_speeds = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.1, 0.15, 0.2, 0.25, 0.3] #possible speeds for the move/go task
        self.stop_y = 8 #vertical location of stop sign (in cm)
        self.stop_sign = None #sign used for speed-stop trials
        self.time_bar_max_height = 550 #maximum height of time bar (in pixels)
        self.time_text = [] #10s and 0s--text next to timer bar
        self.target_pos = 3.35 #position to change colors
        self.response_period_start = None #will keep track of when the current response period began--used to compute response time in output
        self.last_t = None

event_types = {'INSTRUCT_ONSET':1,
    'TASK_ONSET':2,
    'BEEP':3, 
    'DELAY_ONSET':4, 
    'FALSE_START':5, 
    'MOTION_ONSET':6,
    'RESPONSE_PERIOD_ONSET':7,
    'CAR_POSITION_AND_VELOCITY':8,
    'STICK_X':9,
    'STICK_Y':10,
    'MOTION_RESPONSE_END':11,
    'BREAK_ONSET':12,
    'BREAK_END':13,
    'TASK_END':StimToolLib.TASK_END}


def update_target_and_wait(duration):
    start_time = g.clock.getTime()
    now = g.clock.getTime()
    while now - start_time < duration:
        update_target_pos()
        StimToolLib.check_for_esc()
        g.win.flip()
        now = g.clock.getTime()

def three_beeps(trials_left):
    g.car.pos = g.car_start_pos#reset car position
    g.msg.setText(str(trials_left) + ' trial(s) left in this block')
    g.msg.autoDraw = True
    g.timer_msg.setText('Trial starts in 2s')
    g.timer_msg.autoDraw = True
    g.win.flip()
    g.sound_beep1.play()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BEEP'], g.clock.getTime(), 'NA', 'NA', 0, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    update_target_and_wait(1)
    #StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
    g.timer_msg.setText('Trial starts in 1s')
    g.win.flip()
    g.sound_beep1.play()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BEEP'], g.clock.getTime(), 'NA', 'NA', 0, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    update_target_and_wait(1)
    #StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
    g.timer_msg.autoDraw = False
    g.msg.autoDraw = False
    g.sound_beep2.play()
    g.third_beep_time = g.clock.getTime() #in speed-and-stop trials, used to determine reaction time
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BEEP'], g.third_beep_time, 'NA', 'NA', 1, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])

def update_car(): #update position of car based on joy position
    t1 = g.clock.getTime()
    dt = 1.0/60 #based on a single frame--assumes 60 hz frame rate
    #g.this_t = g.clock.getTime()
    #if not g.last_t == None:
    #    dt = g.this_t - g.last_t
    joy_y_pos = -g.joy.getY() #negate so that push is positive, pull is negative
    joy_x_pos = g.joy.getX() #save this value, just in case it ends up being interesting
    #dy =  (g.A*g.car.pos[1] + g.B*joy_y_pos) * dt #change in car position: A term gives resting point (at 0.35) and B gives velocity based on joystick position

    g.dy = g.B * joy_y_pos * dt * dt + (1 - g.C * dt) * g.dy

    #dy = 5 / 60.0
    now = g.clock.getTime()
    if g.response_period_start == None: #first response, record the time and mark the event
        g.response_period_start = now
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['RESPONSE_PERIOD_ONSET'], now, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['CAR_POSITION_AND_VELOCITY'], now, now - g.response_period_start, g.car.pos[1], g.dy * 60, False, g.session_params['parallel_port_address'])
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['STICK_X'], now, now - g.response_period_start, joy_x_pos, 'NA', False, g.session_params['parallel_port_address'])
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['STICK_Y'], now, now - g.response_period_start, joy_y_pos, 'NA', False, g.session_params['parallel_port_address'])

    g.car.pos = [g.car.pos[0], g.car.pos[1] + g.dy] #update car position 
    #g.last_t = g.clock.getTime()
    g.win.flip()

    
    
def update_target_pos():
    g.target.pos = [g.target.pos[0], -g.joy.getY() * 5] #target position: will range from -5 to 5 cm
def move_go_trial(speed):
    motion_per_frame = speed / 60 #speed is in cm/s, motion per frame is cm/frame--assuming 60 hz monitor
    delay_time = random.randint(1, 3) #will wait 1, 2, or 3s before the car starts to move
    #show number of trials left
    g.win.flip() #display initial screen--car on bottom, #trials remaining shown
    start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['DELAY_ONSET'], start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    while g.clock.getTime() - start_time < delay_time:
        StimToolLib.check_for_esc()
        g.win.flip() #have to flip the window to get the recent joystick position
        joy_pos = -g.joy.getY()
        g.target.pos = [g.target.pos[0], joy_pos * 5] #target position: will range from -5 to 5 cm
        if abs(joy_pos) > g.stick_move_threshold:
            g.sound_error.play()
            now = g.clock.getTime()
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FALSE_START'], now, now - start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
            update_target_and_wait(3)
            #StimToolLib.just_wait(g.clock, g.clock.getTime() + 3)
            return False #will cause this trial to be repeated
    #begin car movement and wait for response
    recorded_motion_start = False
    while abs(joy_pos) < g.stick_move_threshold: 
        joy_pos = -g.joy.getY()
        StimToolLib.check_for_esc()
        g.target.pos = [g.target.pos[0], joy_pos * 5] #target position: will range from -5 to 5 cm
        g.car.pos = [g.car.pos[0], g.car.pos[1] + motion_per_frame] #update car position 
        g.win.flip()
        if not recorded_motion_start: #record motion start here so it is *after* the first flip() with the car moved--slightly more accurate (1-16ms) than if this were before the loop
            recorded_motion_start = True
            motion_start_time = g.clock.getTime()
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['MOTION_ONSET'], motion_start_time, 'NA', 'NA', speed, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    g.response_period_start = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['RESPONSE_PERIOD_ONSET'], g.response_period_start, g.response_period_start - motion_start_time , 'NA', g.car.pos[1] + 8, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    done = False
    complete_press_time = None #keep track of when the joy stick made it to the end
    while not done:
        StimToolLib.check_for_esc()
        joy_pos = -g.joy.getY()
        update_car()
        update_target_pos()
        if joy_pos < 1:
            complete_press_time = g.clock.getTime()
        elif g.clock.getTime() - complete_press_time > 0.5: #wait until subject holds the joy stick at the end for 0.5s
            done = True
            g.sound_correct.play()
            now = g.clock.getTime()
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['MOTION_RESPONSE_END'], now, now-g.response_period_start, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
            update_target_and_wait(2)
    g.response_period_start = None
    return True #success, move on to the next trial
    #wait for delay_time--repeat trial if move too soon
    
    #start moving the car and wait for response

def move_go_block(n_trials):
    g.car.autoDraw = True
    #g.target.autoDraw = True
    random.shuffle(g.move_go_speeds)
    speed_idx = 0 #keep track of which speed is next--will be reset to 0 when all speeds have been used
    for i in range(n_trials):
        if speed_idx == len(g.move_go_speeds):
            speed_idx = 0
            random.shuffle(g.move_go_speeds)
        success = False
        while not success: #keep repeating while subject has false starts
            g.target.pos = [g.target.pos[0], 0] 
            three_beeps(n_trials - i)
            success = move_go_trial(g.move_go_speeds[speed_idx])
            update_target_and_wait(1)
        g.trial = g.trial + 1
        speed_idx = speed_idx + 1
    g.car.autoDraw = False
    #g.target.autoDraw = False
    
def update_timer(time_elapsed):
    #draws the timer bar: with time_elapsed=0, should be full length and with time_elapsed=10 will be gone
    #will be blue or green depending on car position (far from or close to stop sign)
    if g.target_pos - g.car.pos[1] > 3 or g.target_pos < g.car.pos[1]:
        pt_bar = g.bar_blue
    else:
        pt_bar = g.bar_green
    if time_elapsed < 10 - 0.04: #when there are two frames left, set height to 0 
        height = (10.0 - time_elapsed) / 10 * g.time_bar_max_height 
    else:
        height = 0 
    pt_bar.size = (g.bar_width, height ) 
    pt_bar.pos = (pt_bar.pos[0], height / 2) #adjust the position, since the position is where the midpoint of the image sits
    pt_bar.draw()
    pass
    
def drive_car(duration, draw_timer):
    #let the subject drive the car for duration seconds
    #also optionally updates the timer bar
    done = False
    while not done:
        update_car() #will set g.response_period_start the first time it's called each trial
        time_elapsed = g.clock.getTime() - g.response_period_start
        StimToolLib.check_for_esc()
        if draw_timer:
            update_timer(time_elapsed)
        if time_elapsed > duration:
            done = True
            g.sound_timeout.play()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 2)
    g.response_period_start = None #reset this for the next time--update_car will set g.response_period_start the first time it's called
            
def speed_stop_trial(trial_length = 10):
    #g.win.flip() #display initial screen--car on bottom
    joy_pos = -g.joy.getY()
    if abs(joy_pos) > g.stick_move_threshold: #will be true if the subject was holding the stick off center at the end of the countdown
            g.sound_error.play()
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FALSE_START'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 3)
            return False #will cause this trial to be repeated
    #wait for response to begin the trial
    while abs(g.joy.getY()) < g.stick_move_threshold:
        StimToolLib.check_for_esc()
        g.win.flip()
    g.response_period_start = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['RESPONSE_PERIOD_ONSET'], g.response_period_start, g.response_period_start - g.third_beep_time , 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    drive_car(trial_length, True)
    return True #success, move on to the next trial
    
def speed_stop_block(n_trials):
    g.stop_sign.autoDraw = True
    g.car.autoDraw = True
    g.time_text[0].autoDraw = True
    g.time_text[1].autoDraw = True
    for i in range(n_trials):
        success = False
        while not success: #keep repeating while subject has false starts
            three_beeps(n_trials - i)
            success = speed_stop_trial()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
        g.trial = g.trial + 1 #increment trial number
    g.car.autoDraw = False
    g.stop_sign.autoDraw=False
    g.time_text[0].autoDraw = False
    g.time_text[1].autoDraw = False
    
    
def speed_stop_block_traction(n_trials):
    """
    Function to run block with traction.
    """
    g.stop_sign.autoDraw = True
    g.car.autoDraw = True
    g.time_text[0].autoDraw = True
    g.time_text[1].autoDraw = True
    for i in range(n_trials):
        # set trial duration
        # trial_length = random.choice([9,10,11])
        g.dy = 0
        trial_length = 10 # All trials are 10 seconds
        success = False
        while not success: #keep repeating while subject has false starts
            three_beeps(n_trials - i)
            success = speed_stop_trial(trial_length)
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
        g.trial = g.trial + 1 #increment trial number
    g.car.autoDraw = False
    g.stop_sign.autoDraw=False
    g.time_text[0].autoDraw = False
    g.time_text[1].autoDraw = False
    
def run_instructions(instruct_schedule_file, g):
    #instructions from schedule file along with audio
    directory = os.path.dirname(instruct_schedule_file)
    fin = open(instruct_schedule_file, 'r')
    lines = fin.readlines()
    fin.close()
    slides = []
    for i in lines:
        slides.append(i.split(','))
    i = 0
    while i < len(slides):
        i = max(0, i + do_one_slide(slides[i], directory, g)) #do_one_slide may increment or decrement i, depending on whether 'enter' or 'backspace' is pressed


def run_instructions_joystick(instruct_schedule_file, g):
    # Instruction for using joysrick
    #core.rush(True)
    directory = os.path.dirname(instruct_schedule_file)
    fin = open(instruct_schedule_file, 'r')
    lines = fin.readlines()
    fin.close()
    slides = []
    for i in lines:
        slides.append(i.split(','))
    isounds=StimToolLib.load_inst_sounds(slides,directory,g)
    i = 0
    g.triggered = False
    while i < len(slides):
        i = max(i + do_one_slide_joystick(slides[i], isounds[i], directory, g), 0) #do_one_slide may increment or decrement i, depending on whether session_params['right'] or session_params['left'] is pressed--don't let them go back on the first slide
    #core.rush(Fals

def do_one_slide_joystick(slide, isound, directory, g):
    """
    
    """
    if slide[0] == 'DEMO':
        g.car.pos = g.car_start_pos#reset car position
        g.stop_sign.autoDraw = True
        g.car.autoDraw = True
        try:
            while g.car.pos[1] < 2.85:
                StimToolLib.check_for_esc()
                g.car.pos = [0, min(g.car.pos[1] + g.B / 120, 2.85)] #g.B is maximum speed in cm/s--go at half speed for demo
                g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
        except StimToolLib.QuitException:
            g.stop_sign.autoDraw = False
            g.car.autoDraw = False
            return -1
        g.stop_sign.autoDraw = False
        g.car.autoDraw = False
        g.win.flip()
        return 1
    if slide[0] == 'PRACTICE':
        g.car.pos = g.car_start_pos
        g.stop_sign.autoDraw = True
        g.car.autoDraw = True
        g.win.flip() #display initial screen--car on bottom
        try:
            drive_car(20, False)
        except StimToolLib.QuitException:
            g.car.autoDraw = False
            g.stop_sign.autoDraw = False
            return -1
        g.car.autoDraw = False
        g.stop_sign.autoDraw = False
        g.win.flip()
        return 1
    image = visual.ImageStim(g.win, image=os.path.join(directory, slide[0]), units = 'pix')
    try:
        image.size = [ g.session_params['screen_x'], g.session_params['screen_y'] ]
    except:
        pass
    s=isound
    advance_time = float(slide[2])
    #if it's -1, don't advance, if it's 0, advance at the end of the sound, if it's positive, advance after that amount of time
    wait_z = False
    if advance_time == -1:
        advance_time = float('inf')
    elif advance_time == 0:
        try:
            advance_time = s.getDuration()
        except AttributeError: #in case there is a None in stead of a sound, just set duration to 0.5
            advance_time = 0.5
    elif advance_time == -2: #wait for a 'z' to advance
        advance_time = float('inf')
        wait_z = True
    
    image.draw()
    g.win.flip()
    k = None #initialize k
    if s:
        s.play()
        advance_time = advance_time - s.getDuration() #since we're waiting for the duration of s, decrease advance_time by that amount--allows for e.g. advance_time of 5s with a sound of 3s->wait 2s after the sound ends
        k = event.waitKeys(keyList = ['z', 'a', 'escape'], maxWait=s.getDuration()) #force the subject to listen to all of the instructions--allow 'z' to skip them or 'a' to force back
    if not k: #if skipped instructions, don't wait to advance afterword
        if g.session_params['allow_instructions_back']: #only allow back if it's specified in the session parameters
            kl = [g.session_params['left'], g.session_params['right'], 'escape', 'z', 'a']
        else:
            kl = [g.session_params['right'], 'escape', 'z', 'a']
        if wait_z: #only advance for a 'z'
            kl = ['z', 'a']
        
        timeout=False
        now=g.clock.getTime()       
        try:
            g.joystick = joystick.Joystick(0) 
            while 1:
                #if not g.session_params['joystick']: break # Break out of this if wer're not using a joystick
                if g.clock.getTime() > now + advance_time:
                    timeout=True 
                    break
                k=event.getKeys(keyList = kl)
                if k!=[]:
                    break
                if g.joystick.getButton(g.session_params['joy_forward']) or g.joystick.getButton(g.session_params['joy_backward']):
                    break
                image.draw()
                event.clearEvents()
                g.win.flip()
        except (AttributeError,IndexError):
            k = event.waitKeys(keyList = kl, maxWait=advance_time)

    if s: #stop the sound if it's still playing
        s.stop()
    try:
        if g.joystick.getButton(g.session_params['joy_forward']) or timeout:
            retval = 1
        elif g.joystick.getButton(g.session_params['joy_backward']):
            retval = -1
    except (AttributeError, UnboundLocalError, IndexError):
        joystick_not_used=True
                
    if k == None or k == []: #event timeout
        print('')
    elif k[0] == 'z':
        retval = 1
    elif k[0] == 'a':
        retval = -1
    elif k[0] == g.session_params['right']:
        print(k[0])
        retval = 1
    elif k[0] == g.session_params['left']:
        retval = -1
    elif k[0] == 'escape':
        raise QuitException()
    return retval

def do_one_slide(slide, directory, g):
    if slide[0] == 'DEMO':
        g.car.pos = g.car_start_pos#reset car position
        g.stop_sign.autoDraw = True
        g.car.autoDraw = True
        try:
            while g.car.pos[1] < 2.85:
                StimToolLib.check_for_esc()
                g.car.pos = [0, min(g.car.pos[1] + g.B / 120, 2.85)] #g.B is maximum speed in cm/s--go at half speed for demo
                g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
        except StimToolLib.QuitException:
            g.stop_sign.autoDraw = False
            g.car.autoDraw = False
            return -1
        g.stop_sign.autoDraw = False
        g.car.autoDraw = False
        g.win.flip()
        return 1
    if slide[0] == 'PRACTICE':
        g.car.pos = g.car_start_pos
        g.stop_sign.autoDraw = True
        g.car.autoDraw = True
        g.win.flip() #display initial screen--car on bottom
        try:
            drive_car(20, False)
        except StimToolLib.QuitException:
            g.car.autoDraw = False
            g.stop_sign.autoDraw = False
            return -1
        g.car.autoDraw = False
        g.stop_sign.autoDraw = False
        g.win.flip()
        return 1
    image = visual.ImageStim(g.win, image=os.path.join(directory, slide[0]))
    if slide[1] == 'None':
        s = None
    else:
        s = sound.Sound(value = os.path.join(directory, slide[1]), volume=g.session_params['instruction_volume'])
    advance_time = float(slide[2])
    #if it's -1, don't advance, if it's 0, advance at the end of the sound, if it's positive, advance after that amount of time
    if advance_time == -1:
        advance_time = float('inf')
    elif advance_time == 0:
        try:
            advance_time = s.getDuration()
        except AttributeError: #in case there is a None in stead of a sound, just set duration to 0.5
            advance_time = 0.5
    image.draw()
    g.win.flip()
    k = None
    if s:
        s.play()
        advance_time = advance_time - s.getDuration() #since we're waiting for the duration of s, decrease advance_time by that amount--allows for e.g. advance_time of 5s with a sound of 3s->wait 2s after the sound ends
        k = event.waitKeys(keyList = ['z', 'a', 'escape'], maxWait=s.getDuration()) #force the subject to listen to all of the instructions--allow 'z' to skip them or 'a' to force back
    if not k: #if skipped instructions, don't wait to advance afterword
        if g.session_params['allow_instructions_back']: #only allow back if it's specified in the session parameters
            kl = [g.session_params['left'], g.session_params['right'], 'escape']
        else:
            kl = [g.session_params['right'], 'escape']
        k = event.waitKeys(keyList = kl, maxWait=advance_time)
    if s:
        s.stop()
    if k == None: #event timeout
        return 1
    if k[0] == 'z':
        retval = 1
    if k[0] == 'a':
        retval = -1
    if k[0] == g.session_params['right']:
        retval = 1
    if k[0] == g.session_params['left']:
        retval = -1
    if k[0] == 'escape':
        raise StimToolLib.QuitException()
    return retval
    
    
def move_go_instruct(n_trials):
    run_instructions_joystick(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'DR_instruct_schedule_MG.csv'), g)
    if g.session_params['scan']:
        StimToolLib.wait_scan_start(g.win)
    else:
        StimToolLib.wait_start(g.win)
    
def speed_stop_instruct(n_trials):
    run_instructions_joystick(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'DR_instruct_schedule_JOY_SS.csv'), g)
    if g.session_params['scan']:
        StimToolLib.wait_scan_start(g.win)
    else:
        StimToolLib.wait_start(g.win)

def do_one_block(block_type, block_length):
    g.trial_type = block_type #set trial type to be written to output file
    if block_type == '0': #move_go_instructions
        start_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['INSTRUCT_ONSET'], start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        move_go_instruct(block_length)
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TASK_ONSET'], now, now - start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    if block_type == '1': #move_go_block
        g.trial_type = 1 #set trial type for output for this block
        move_go_block(block_length)
    if block_type == '2': #speed_stop_instructions
        start_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['INSTRUCT_ONSET'], start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        speed_stop_instruct(block_length)
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TASK_ONSET'], now, now - start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
    if block_type == '3': #speed_stop_block
        g.trial_type = 3 #set trial type for output for this block
        speed_stop_block(block_length)

    # Speed Stop with differente traction
    # foramt for block type would be something like 30a, 32b, 31c
    # 1st digit means it's a speed stop block
    # 2nd digit means it's the traction control value (g.C)
    if (len(block_type) == 2):
        g.trial_type = block_type

        # Ths LSB is the traction g.C value. 30 = 0, 31 = 1, 32 = 2
        g.C = float(block_type[1])
    
        speed_stop_block_traction(block_length)

    if block_type == '4': #break
        start_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BREAK_ONSET'], start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        StimToolLib.show_instructions(g.win, ['Now please take a 5 second break'])
        end_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BREAK_END'], end_time, end_time - start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        g.win.flip()
    
    if block_type == '5': #break with fixation , specified duration
        start_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BREAK_ONSET'], start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        g.win.flip()
        g.fix.draw()
        g.win.flip()
        StimToolLib.just_wait(g.clock,start_time + float(block_length) )
        end_time = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BREAK_END'], end_time, end_time - start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        g.win.flip()
    StimToolLib.just_wait(g.clock, g.clock.getTime() + 1) #one second pause at the end of each block so the next one doesn't start immediately

def run(session_params, run_params):
    global g
    g = GlobalVars()
    g.session_params = session_params
    g.run_params = StimToolLib.get_var_dict_from_file(os.path.dirname(__file__) + '/DR.Default.params', {})
    g.run_params.update(run_params)
    try:
        run_try()
        g.status = 0
    except StimToolLib.QuitException as q:
        g.status = -1
    StimToolLib.task_end(g)
    return g.status
        
def run_try():  
#def run_try(SID, raID, scan, resk, run_num='1'):
    
    #setup the joystick
    
    schedules = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.schedule')]
    if not g.session_params['auto_advance']:
        myDlg = gui.Dlg(title="DR")
        myDlg.addField('Run Number', choices=schedules, initial=str(g.run_params['run']))
        myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # then the user pressed OK
            thisInfo = myDlg.data
        else:
            print('QUIT!')
            return -1#the user hit cancel so exit 
        g.run_params['run'] = thisInfo[0]
    StimToolLib.general_setup(g)
    joystick.backend= g.win.winType
    nJoysticks=joystick.getNumJoysticks()
    if nJoysticks>0:
        g.joy = joystick.Joystick(0)
    else:
        g.win.close()
        #try:
        StimToolLib.error_popup("You don't have a joystick connected?")
        #except StimToolLib.QuitException:
        #    return -1
            
    
    #g.resk = resk

    g.timer_msg = visual.TextStim(g.win,text="",units='pix',pos=[0,-50],color=[1,1,1],height=30,wrapWidth=int(1600))
    schedule_file = os.path.join(os.path.dirname(__file__), g.run_params['run'])
    #param_file = os.path.join(os.path.dirname(__file__),'T1000_DR_Schedule' + str(g.run_params['run']) + '.csv')
    block_types,junk,block_lengths,junk = StimToolLib.read_trial_structure(schedule_file, g.win, g.msg)
    block_lengths = block_lengths[0] 

    
    start_time = data.getDateStr()
    
    param_file = g.run_params['run'][0:-9] + '.params' #every .schedule file can (probably should) have a .params file associated with it to specify running parameters (including part of the output filename)
    StimToolLib.get_var_dict_from_file(os.path.join(os.path.dirname(__file__), param_file), g.run_params)
    g.prefix = StimToolLib.generate_prefix(g)
    fileName = os.path.join(g.prefix + '.csv')

    # Set Params if any
    try:
        g.stick_move_threshold = g.run_params['stick_move_threshold']
    except:
        pass
    
    #g.prefix = 'DR-' + g.session_params['SID'] + '-Admin_' + g.session_params['raID'] + '-run_' + str(g.run_params['run']) + '-' + start_time 
    #fileName = os.path.join(os.path.dirname(__file__), 'data/' + g.prefix +  '.csv')
    g.output = open(fileName, 'w')
    
    sorted_events = sorted(event_types.items(), key=lambda item: item[1])
    g.output.write('Administrator:,' + g.session_params['admin_id'] + ',Original File Name:,' + fileName + ',Time:,' + start_time + ',Parameter File:,' +  schedule_file + ',Event Codes:,' + str(sorted_events) + '\n')
    g.output.write('trial_number,trial_type,event_code,absolute_time,response_time,response,result\n')

    g.car = visual.ImageStim(g.win, os.path.join(os.path.dirname(__file__),'media/car2.bmp'), units='cm', interpolate=True, mask=os.path.join(os.path.dirname(__file__),'media/car_mask.bmp'))
    g.bar_green = visual.ImageStim(g.win, os.path.join(os.path.dirname(__file__),'media/bar_green.png'), pos=(g.bar_x, 0), units='pix')
    g.bar_blue = visual.ImageStim(g.win, os.path.join(os.path.dirname(__file__),'media/bar_blue.png'), pos=(g.bar_x, 0), units='pix')
    g.stop_sign = visual.ImageStim(g.win, os.path.join(os.path.dirname(__file__),'media/stop.png'), pos=(0, g.stop_y), units='cm', interpolate=True)
    g.target = visual.ImageStim(g.win, os.path.join(os.path.dirname(__file__),'media/circle_white.png'), pos=[6, 0], units='cm')
    g.sound_correct = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/correctsound.aiff'), volume=0.08)
    g.sound_error = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/errorsound.aiff'), volume=0.08)
    g.sound_double_error = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/doubleerrorsound.aiff'), volume=0.08)
    g.sound_beep1 = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/beep1.aiff'), volume=0.08)
    g.sound_beep2 = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/beep2.aiff'), volume=0.08)
    g.sound_timeout = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/timeoutsound.aiff'), volume=0.08)
    
    g.time_text.append(visual.TextStim(g.win, text="10s", units='pix', height=25, color=[1,1,1], pos=[g.bar_x + 45,550]))
    g.time_text.append(visual.TextStim(g.win, text="0s", units='pix', height=25, color=[1,1,1], pos=[g.bar_x + 45,0]))
    
    g.fix = visual.TextStim(g.win, text="X", units='pix', height=50, color=[1,1,1], pos=[0,0], bold=True)
    
    StimToolLib.task_start(StimToolLib.DRIVE_CODE, g)
    g.win.flip()
    g.trial = 0 #initialize trial number
    #StimToolLib.show_title(g.win, g.title)
    for i in range(len(block_types)):     
        do_one_block(block_types[i], int(block_lengths[i]))




