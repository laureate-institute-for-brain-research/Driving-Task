from psychopy import prefs
import sys, os, ctypes
prefs.general['audioLib'] = [u'pyo', u'pygame']
from psychopy import sound, core, visual


prefs.general[u'audioDriver'] = [u'ASIO4ALL', u'ASIO', u'Audigy']

s = sound.Sound(value='SS_50ms.wav', volume=0.1)

win = visual.Window(fullscr=False, screen=1,color=(-1,-1,-1), waitBlanking=True, colorSpace='rgb',winType='pyglet', allowGUI=False)
x = visual.TextStim(win, text="X", units='pix', height=50, color=[1,1,1], pos=[0,0], bold=True)    


for i in range(20):
    if i % 2 == 0:
        x.draw()
    
    win.flip()
    s.play()

    core.wait(1)

win.close()
core.quit()