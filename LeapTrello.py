#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys, os, math, random
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
    user_auth_token = 'fe9136da8f4bd3f9400996bfd21077bf73250e884a642800360a26915ed3a315'
    board_id = '52120adfbcec5a8c6a0018a8'
    card_id = '521349f9204ffcad710002c0'
    list_id = '52120adfbcec5a8c6a0018ab'
    client = Client( api_key, user_auth_token )

    def __init__( self ) :
        print("Initialized Trello Client...")

    def getCardInformation( self, card_id, query_params = {} ):
        return MyCard( self.client, card_id ).getCardInformation(query_params)

    def getCards( self ):
        board = Board( self.client, self.board_id)
        return board.getCards()

    def getLists( self ):
        board = Board( self.client, self.board_id)
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
    def __init__(self, client, app):
        QtGui.QMainWindow.__init__(self)

        self.lists = []
        self.app = app
        self.client = client

        self.mainposx = 100
        self.mainposy = 100
        self.mainwidth = 1200
        self.mainheight = 800

        self.currentCard = None

        self.initUI()

    def initUI(self):           
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
               
        img = QtGui.QLabel(self)
        img.setGeometry(5, self.mainheight - 50 - 5, 200, 50)
        img.setPixmap(QtGui.QPixmap(os.getcwd() + "/resources/trellol_logo_small.png"))

        layout = self.setContent(self.client)
        window = QtGui.QWidget();
        window.setLayout(layout)
        self.setCentralWidget(window)
        
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAcceptDrops(True)
        
        self.center()
        self.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(self.mainposx, self.mainposy, self.mainwidth, self.mainheight)        
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def setContent(self, client):
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(20)

        trello_lists = client.getLists()
        for y in range(0, len(trello_lists)):
            list = trello_lists[y]
            cards = client.getCardsByList( list.id )
            hbox.addLayout( TrelloList( self, list.name, cards ) ) 

        self.currentCard = hbox.itemAt(0).itemAt(1).widget()
        return hbox
        
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()
        elif key == QtCore.Qt.Key_F:
            if self.windowState() & QtCore.Qt.WindowFullScreen:
                self.showNormal()
            else:
                self.showFullScreen()

        return QtGui.QWidget.keyPressEvent(self, event)

    def dragEnterEvent(self, e):  
        e.accept()

    def dropEvent(self, e):
        position = e.pos()
        e.source().move(position - e.source().rect().center())
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

class TrelloCard(QtGui.QLabel):    
    def __init__(self, parent, id, name):
        QtGui.QLabel.__init__(self, parent)
        self.setText( "id: " + id + "\nname: " + name)
        self.colorDeselect = "#AAA"
        self.colorSelect = "#A44"
        self.deselect()
        self.setMouseTracking(True)
        self.parent = parent
        self.setFixedHeight(80)
        
    def select(self):
        self.setStyleSheet("QWidget { background-color: %s }" % self.colorSelect)

    def deselect(self):
        self.setStyleSheet("QWidget { background-color: %s }" % self.colorDeselect)

    def getCentroid(self):
        x,y,w,h = self.x(), self.y(), self.width(), self.height()
        return (x + (w/2), y + (h/2))

    def getDistTo(self, x, y):
        thisx, thisy = self.getCentroid()
        dist = math.sqrt( (math.pow(thisx - x, 2) + math.pow(thisy - y, 2)))
        return dist

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            mimeData = QtCore.QMimeData()
            pixmap = QtGui.QPixmap.grabWidget(self)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap);
            drag.setHotSpot(event.pos())
            
            dropAction = drag.start(QtCore.Qt.MoveAction)

        elif (self.parent.currentCard is not self): # TODO: assumes no buttons
            self.parent.currentCard.deselect()
            self.parent.currentCard = self
            self.select()

        return QtGui.QFrame.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        QtGui.QLabel.mousePressEvent(self, event)

    def __str__(self):
        return "Card @  %s" % (self.geometry())


class TrelloList(QtGui.QFormLayout):
    def __init__(self, parent, name, cards):
        QtGui.QFormLayout.__init__(self)
        self.addWidget( TrelloListHeader( parent, name ) )
        for card in cards:
            #TODO: parent
            self.addWidget( TrelloCard( parent, card.id, card.name) )

class TrelloListHeader(QtGui.QLabel):
    def __init__(self, parent, text):
        QtGui.QLabel.__init__(self, parent)
        self.setText(text)
        self.setStyleSheet("QWidget { font: bold 15px }")

def main():    
    app = QtGui.QApplication(sys.argv)
    client = TrelloClient()
    board = TrelloBoard(client, app)
    app.installEventFilter(board) # TODO: ???

    listener = LeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"

if __name__ == "__main__":
    main()
