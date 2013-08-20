#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from pymouse import PyMouse
from PyQt4 import QtGui, QtCore

from trolly.client import Client
from trolly.organisation import Organisation
from trolly.board import Board
from trolly.list import List
from trolly.card import Card
from trolly.checklist import Checklist
from trolly.member import Member
from trolly import ResourceUnavailable

class LeapListener(Leap.Listener):

    mouse = PyMouse()
    width_in_pixels, height_in_pixels = mouse.screen_size()
    screen_wc = (width_in_pixels/2)
    screen_hc = (height_in_pixels/2)
    downPressed = False  

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
            fingers = frame.hands[0].fingers
            xpos = ypos = 0

            if not fingers.empty:
                # Calculate the hand's average finger tip position
                avg_pos = Leap.Vector()
                for finger in fingers:
                    avg_pos += finger.tip_position
                avg_pos /= len(fingers)
                x,y,z = avg_pos[0],avg_pos[1],avg_pos[2]

                print "(%5f,%5f) %5f" % (x, z, y)

                rawxpos = self.screen_wc + x*15
                rawypos = self.screen_hc + z*15

                xpos = max(min(rawxpos, self.width_in_pixels),0)
                ypos = max(min(rawypos, self.height_in_pixels),0)

                
            self.mouse.move(xpos, ypos)
     
            # TAP
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_KEY_TAP:

                    if self.downPressed:
                        self.mouse.press(xpos,ypos)
                        print "UP"
                    else:
                        self.mouse.release(xpos,ypos)
                        print "DOWN"
                    
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

class TrelloClient:

    api_key = 'cae2c8a0e8fff08a3031310959cb94c8'
    user_auth_token = 'edd28ce8296002f04b3e0d8a06674a27bacae743aba77e15c8eec353c13541a8'
    board_id = '52120adfbcec5a8c6a0018a8'
    card_id = '521349f9204ffcad710002c0'
    list_id = '52120adfbcec5a8c6a0018ab'
    client = Client( api_key, user_auth_token )

    def __init__( self ) :
        print("Initialized Trello Client...")

    def getCardInformation( self, card_id, query_params = {} ):
        return MyCard( self.client, card_id ).getCardInformation(query_params)

    def getLists( self, board_id ):
        board = Board( self.client, board_id)
        return board.getLists()

    def getCardsByList( self, list_id ):
        list = List( self.client, list_id )
        return list.getCards()
 
    def putCardToList( self, card_id, list_id ):
        card = MyCard( self.client, card_id)
        card.putToList({ 'value' : list_id })
    

class MyCard( Card ):

    def __init__( self, trello_client, card_id, name = '' ):
        super( MyCard, self ).__init__( trello_client, card_id, name )

    def putToList( self, query_params = {} ):
        card_json = self.fetchJson(
            uri_path = self.base_uri + '/idList',
            http_method = 'PUT',
            query_params = query_params
        )
        return self.createCard( card_json )


class TrelloBoard(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.initUI()

    def initUI(self):           
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground) # Enable later for max awesome        
        self.center()
        self.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(100, 100, 1200, 800)        
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()
        elif key == QtCore.Qt.Key_F:
            if self.windowState() & QtCore.Qt.WindowFullScreen:
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            QtGui.QWidget.keyPressEvent(self, event)

def main():    
    app = QtGui.QApplication(sys.argv)
    client = TrelloClient()
    board = TrelloBoard()

    listener = LeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"

if __name__ == "__main__":
    main()
