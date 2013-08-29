#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
LeapListener

A Leap Motion interface with palm position tracking and simple gestures

"""

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from pymouse import PyMouse

class LeapListener(Leap.Listener):

    def __init__(self):
        Leap.Listener.__init__(self)

        self.mouse = PyMouse()
        self.screenW, self.screenH = self.mouse.screen_size()
        self.screenCenterW = self.screenW / 2
        self.screenCenterH = self.screenH / 2

        self.downPressed = False    
        self.pointingMultiplier = 15
                
    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES)

    def on_disconnect(self, controller):
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def on_frame(self, controller):
        frame = controller.frame()

        if not frame.hands.empty:
            hpos = frame.hands[0].palm_position
            x,y,z = hpos[0],hpos[1],hpos[2]
                
            rawxpos = self.screenCenterW + x*self.pointingMultiplier
            rawypos = self.screenCenterH + z*self.pointingMultiplier
            xpos = max(min(rawxpos, self.screenW),0)
            ypos = max(min(rawypos, self.screenH),0)
                
            self.mouse.move(xpos, ypos)
     
            # TAP
            if not frame.gestures().empty :
                for gesture in frame.gestures():
                    if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                        if not self.downPressed:
                            self.mouse.press(xpos,ypos)
                        else:
                            self.mouse.release(xpos,ypos)
                    
                        self.downPressed = not self.downPressed
                                    
    def state_string(self, state):        
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"
