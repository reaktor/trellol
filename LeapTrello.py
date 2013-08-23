#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys, os, math, time
from PyQt4 import QtGui, QtCore
from LeapListener import LeapListener

from trolly.client import Client
from trolly.board import Board
from trolly.list import List
from trolly.card import Card
# from trolly.organisation import Organisation
# from trolly.checklist import Checklist
# from trolly.member import Member
# from trolly import ResourceUnavailable

class TrelloBoard(QtGui.QMainWindow):  
    def __init__(self, client, app, boardId):
        QtGui.QMainWindow.__init__(self)

        self.lists = []
        self.app = app
        self.client = client
        self.boardId = boardId

        self.board = Board(client, boardId)

        self.mainposx = 100
        self.mainposy = 100
        self.mainwidth = 1200
        self.mainheight = 800

        self.logo = QtGui.QLabel(self)
        self.logo.setPixmap(QtGui.QPixmap(os.getcwd() + "/resources/trellol_logo_small.png"))
        
        self.initUI()

    def initUI(self):           
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.backgroundColor = "#B8C0CC"
        self.setStyleSheet("QMainWindow { background-color: %s }" % self.backgroundColor)
        self.render() 
        self.center()
        self.show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(self.mainposx, self.mainposy, self.mainwidth, self.mainheight)        
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def render(self):
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(0)
        lists = self.board.getLists()
        for rawlist in lists:            
            cards = rawlist.getCards()
            hbox.addWidget( TrelloList( self, self.client, rawlist.id, rawlist.name, cards ) ) 

        self.window = QtGui.QWidget();
        self.window.setLayout(hbox)
        self.setCentralWidget(self.window)
        self.currentCard = None

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
    def __init__(self, tlist, card_id, name):
        QtGui.QLabel.__init__(self)
        self.id = card_id
        self.name = name
        self.setText(name)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.borderColor = "#000000"
        self.colorDeselect = "#FFF"
        self.colorSelect = "#4675E3"
        self.deselect()
        self.tlist = tlist
        self.setMouseTracking(True)
        self.setFixedHeight(80)
        self.setFixedWidth(220)

    def select(self):
        self.setStyleSheet("QWidget { font: 20px; color: white; background-color: %s; border:2px solid %s; border-radius: 3px;}" % (self.colorSelect, self.borderColor))

    def deselect(self):
        self.setStyleSheet("QWidget { font: 20px; background-color: %s; border:1px solid %s; border-radius: 3px;}" % (self.colorDeselect,self.borderColor))

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

        #TODO: QtCore.Qt.NoButton in OS X ???
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
    def __init__(self, board, client, list_id, name, cards):
        QtGui.QWidget.__init__(self)
        self.board = board
        self.client = client
        self.id = list_id

        self.form = QtGui.QFormLayout()
        self.form.addWidget(TrelloListHeader(self, name))
        self.form.addWidget(TrelloListCards(self, cards))
        self.setPadding(self.form)

        self.setLayout(self.form)
        self.setAcceptDrops(True)

    def setPadding(self, layout):
        layout.setHorizontalSpacing(0)
        layout.setContentsMargins(0,0,0,0)

    def dragEnterEvent(self, e): 
        self.board.currentCard.setParent(None)
        self.form.addWidget(self.board.currentCard)
        e.accept()

    def dropEvent(self, e):
        Card(self.client, e.source().id).updateCard({ 'idList' : self.id})

        # TODO: Prettify the drop event
        # position = e.pos()        
        # e.source().move(position - e.source().rect().center())
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

class TrelloListHeader(QtGui.QLabel):
    def __init__(self, tlist, text):
        QtGui.QLabel.__init__(self, tlist)
        self.tlist = tlist
        self.setText(text)
        self.setStyleSheet("QLabel { font: bold 15px; }") 
        self.setFixedWidth(220)
        self.setFixedHeight(70)

class TrelloListCards(QtGui.QWidget):
    def __init__( self, tlist, cards):
        QtGui.QWidget.__init__(self, tlist)
        self.tlist = tlist

        layout = QtGui.QFormLayout()
        self.setStyleSheet("QFormLayout { background-color: #000 }")
        self.clearPadding(layout)

        for card in cards:
            layout.addWidget(TrelloCard(tlist, card.id, card.name))
        self.setLayout(layout)

    def clearPadding(self, layout):
        layout.setHorizontalSpacing(0)
        layout.setContentsMargins(0,0,0,0)

class WorkThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
  
    def run(self):
        while(True):
            time.sleep(5)
            self.emit(QtCore.SIGNAL('update()'))

def main():    
    apiKey = 'cae2c8a0e8fff08a3031310959cb94c8'
    userAuthToken = '9bbf9f6e2b89d7c098eca47f2265609ee4c04fb317e6f1da1c2ffd5b0daba448'
    client = Client(apiKey, userAuthToken)

    app = QtGui.QApplication(sys.argv)

    boardId = '52120adfbcec5a8c6a0018a8'
    board = TrelloBoard(client, app, boardId)

    #workThread = WorkThread()
    #QtCore.QObject.connect( workThread, QtCore.SIGNAL("update()"), board.render)
    #workThread.start()

    listener = LeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"

if __name__ == "__main__":
    main()
