################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

import Leap, sys
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

from Xlib import X, display

class SampleListener(Leap.Listener):

    d = display.Display()
    s = d.screen()
    s.root.grab_pointer(1, X.ButtonPressMask | X.ButtonReleaseMask | X.Button1MotionMask,
                        X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE, X.CurrentTime)
    screen_wc = (s.width_in_pixels/2)
    screen_hc = (s.height_in_pixels/2)

    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"

        # Enable gestures
        # controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        if not frame.hands.empty:

            # print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
            #     frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures()))            

            # Get the first hand
            hand = frame.hands[0]

            # Check if the hand has any fingers
            fingers = hand.fingers
            if not fingers.empty:
                # Calculate the hand's average finger tip position
                avg_pos = Leap.Vector()
                for finger in fingers:
                    avg_pos += finger.tip_position
                avg_pos /= len(fingers)
                x,y,z = int(avg_pos[0]),int(avg_pos[1]),int(avg_pos[2])
                
                x_desc = "L" * -int(x/25) if x < 0 else "R" * int(x/25) 
                y_desc = "D" * int(y/10) if y < 100 else "U" * max(10, int(y/25))
                z_desc = "F" * -int(z/25) if z < 0 else "B" * int(z/25) 

                xpos = self.screen_wc + x*5
                ypos = self.screen_hc + z*5

                desc = "%s %s %s" % (x_desc, y_desc, z_desc)
                print "ahpos %4d %4d %4d | %5s %10s %5s | %d %d" % (x,y,z, x_desc, y_desc, z_desc, xpos, ypos)

                new_x = max(min(xpos, self.s.width_in_pixels),0)
                new_y = max(min(ypos, self.s.height_in_pixels),0)
                self.s.root.warp_pointer(new_x, new_y)
                self.d.sync()

            # Get the hand's normal vector and direction
            normal = hand.palm_normal
            direction = hand.direction

            # TAP
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                    keytap = KeyTapGesture(gesture)
                    print "Key Tap id: %d, %s, position: %s, direction: %s" % (
                            gesture.id, self.state_string(gesture.state),
                            keytap.position, keytap.direction )
                    self.s.root.send_event()
                    
                    
    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # Remove the sample listener when done
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
