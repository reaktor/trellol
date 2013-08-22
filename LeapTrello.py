#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys, os, math, collections
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

# TODO: uniform name convention, underscores or camelcase

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
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_KEY_TAP:

                    if self.downPressed:
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

class TrelloClient:

    api_key = 'cae2c8a0e8fff08a3031310959cb94c8'
    user_auth_token = '9bbf9f6e2b89d7c098eca47f2265609ee4c04fb317e6f1da1c2ffd5b0daba448'
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

        self.logo = QtGui.QLabel(self)
        self.logo.setPixmap(QtGui.QPixmap(os.getcwd() + "/resources/trellol_logo_small.png"))

        self.currentCard = None
        
        self.initUI()

    def initUI(self):           
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.backgroundColor = "#275E79"
        self.setStyleSheet("QMainWindow { background-color: %s }" % self.backgroundColor)

        layout = self.setContent(self.client)
        window = QtGui.QWidget();
        window.setLayout(layout)
        self.setCentralWidget(window)
        
        self.center()
        self.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(self.mainposx, self.mainposy, self.mainwidth, self.mainheight)        
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def setContent(self, client):
        hbox = QtGui.QHBoxLayout()

        trelloLists = client.getLists()
        for y in range(0, len(trelloLists)):
            trelloList = trelloLists[y]
            cards = client.getCardsByList( trelloList.id )
            hbox.addWidget( TrelloList( self, trelloList.name, cards ) ) 

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

    def resizeEvent(self, e):
        self.logo.setGeometry(5, self.height() - 50 - 5, 200, 50)
        

class TrelloCard(QtGui.QLabel):    
    def __init__(self, tlist, id, name):
        QtGui.QLabel.__init__(self)
        self.setText( "id: " + id + "\nname: " + name)
        self.backgroundColor = "#FFF"
        self.colorDeselect = "#FFF"
        self.colorSelect = "#3D6E86"
        self.deselect()
        self.tlist = tlist
        self.setMouseTracking(True)
        self.setFixedHeight(60)
        
    def select(self):
        self.setStyleSheet("QWidget { background-color: %s; border:2px solid %s; border-radius: 5px;}" % (self.backgroundColor,self.colorSelect))

    def deselect(self):
        self.setStyleSheet("QWidget { background-color: %s; border:2px solid %s; border-radius: 5px;}" % (self.backgroundColor,self.colorDeselect))

    def getCentroid(self):
        x,y,w,h = self.x(), self.y(), self.width(), self.height()
        return (x + (w/2), y + (h/2))

    def getDistTo(self, x, y):
        thisx, thisy = self.getCentroid()
        dist = math.sqrt( (math.pow(thisx - x, 2) + math.pow(thisy - y, 2)))
        return dist

    def mouseMoveEvent(self, event):
        if (self.tlist.board.currentCard is not self):
            if (self.tlist.board.currentCard is not None):
                self.tlist.board.currentCard.deselect()
            self.tlist.board.currentCard = self
            self.select()

        if event.buttons() == QtCore.Qt.LeftButton:
            mimeData = QtCore.QMimeData()
            pixmap = QtGui.QPixmap.grabWidget(self)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())        
            drag.exec_(QtCore.Qt.MoveAction)

    def mousePressEvent(self, event):
        QtGui.QLabel.mousePressEvent(self, event)

    def __str__(self):
        return "Card @  %s" % (self.geometry())


class TrelloList(QtGui.QWidget):
    def __init__(self, board, name, cards):
        QtGui.QWidget.__init__(self)
        self.board = board

        self.form = QtGui.QFormLayout()
        self.form.addWidget(TrelloListHeader(self, name))
        self.form.addWidget(TrelloListCards(self, cards))
        self.setLayout(self.form)
        
        self.setAcceptDrops(True)


    def dragEnterEvent(self, e):          
        self.board.currentCard.setParent(None)
        self.form.addWidget(self.board.currentCard)
        e.accept()

    def dropEvent(self, e):
        # Prettify the drop event
        position = e.pos()
        # e.source().move(position - e.source().rect().center())
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

class TrelloListHeader(QtGui.QWidget):
    def __init__(self, tlist, text):
        QtGui.QLabel.__init__(self)
        self.tlist = tlist

       # self.setText(text)
        self.setStyleSheet("QWidget { font: bold 15px }") 

class TrelloListCards(QtGui.QWidget):
    def __init__( self, tlist, cards):
        QtGui.QWidget.__init__(self)
        self.tlist = tlist

        layout = QtGui.QFormLayout()
        for card in cards:
            layout.addWidget(TrelloCard(tlist, card.id, card.name))
        self.setLayout(layout)

def main():    
    app = QtGui.QApplication(sys.argv)
    client = TrelloClient()
    board = TrelloBoard(client, app)

    listener = LeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"

if __name__ == "__main__":
    main()
