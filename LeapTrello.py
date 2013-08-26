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

BG_GRAY="#B8C0CC"
TRELLO_BLUE="#1C678C"


class TrelloBoard(QtGui.QMainWindow):  
    TrelloBoardStyle=\
        "QMainWindow { background-color: %s; }" % (BG_GRAY)

    def __init__(self, client, app, boardId):
        QtGui.QMainWindow.__init__(self)

        self.lists = []
        self.app = app
        self.client = client
        self.boardId = boardId

        self.board = Board(client, boardId)

        self.render()
        self.style()
        self.show()

    def style(self):           
        self.setWindowTitle('Leap Motion + Trello')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet(self.TrelloBoardStyle)        

        self.logo = QtGui.QLabel(self)
        self.logo.setPixmap(QtGui.QPixmap(os.getcwd() + "/resources/trellol_logo_small.png"))

        self.cursorImg = QtGui.QPixmap(os.getcwd() + "/resources/BallCursor.png")
        #self.cursorImg = QtGui.QPixmap(os.getcwd() + "/resources/NullCursor.png")
        self.setCursor(QtGui.QCursor(self.cursorImg, -1, -1))
        
        self.center()

    def center(self):
        mainposx = 100 #TODO conf file
        mainposy = 100
        mainwidth = 1200
        mainheight = 800

        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(mainposx, mainposy, mainwidth, mainheight)        
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
        # TODO conf file
        self.logo.setGeometry(5, self.height() - 50 - 5, 200, 50)


class TrelloList(QtGui.QWidget):
    def __init__(self, board, client, list_id, name, cards):
        QtGui.QWidget.__init__(self)
        self.board = board
        self.client = client
        self.id = list_id
        self.name = name

        layout = QtGui.QFormLayout()
        layout.addWidget(TrelloListHeader(self.name))
        layout.addWidget(TrelloListCards(self, cards))
        self.setLayout(layout)

        self.style()
        
        self.setAcceptDrops(True)

    def style(self):
        self.layout().setHorizontalSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)        

    def dragEnterEvent(self, e): 
        self.board.currentCard.setParent(None)
        self.form.addWidget(self.board.currentCard)
        e.accept()

    def dropEvent(self, e):
        # TODO Make async
        Card(self.client, e.source().id).updateCard({ 'idList' : self.id})

        # TODO: Prettify the drop event
        # position = e.pos()        
        # e.source().move(position - e.source().rect().center())
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()


class TrelloCard(QtGui.QLabel):
    # TODO conf file    
    TrelloCardDeselectStyle=\
        "TrelloCard { font: 20px; background-color: #FFF; border:1px solid #000; border-radius: 3px;}"
    
    TrelloCardSelectStyle=\
        "TrelloCard { font: 20px; color:white; background-color: #4675E3; border:2px solid #000; border-radius:3px;}"

    def __init__(self, tlist, card_id, name):
        QtGui.QLabel.__init__(self)
        self.id = card_id
        self.name = name
        self.tlist = tlist

        self.setText(name)
        self.setMouseTracking(True)

        self.style()

    def style(self):
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.deselect()
        self.setFixedHeight(80)
        self.setFixedWidth(220)
        
    def select(self):
        self.setStyleSheet(self.TrelloCardSelectStyle)

    def deselect(self):
        self.setStyleSheet(self.TrelloCardDeselectStyle)

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
        if not event.buttons() == QtCore.Qt.NoButton: #QtCore.Qt.LeftButton:
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


class TrelloListHeader(QtGui.QLabel):
    TrelloListHeaderStyle="QLabel { font: bold 15px; }"

    def __init__(self, text):
        QtGui.QLabel.__init__(self)

        self.setText(text)
        self.style()

    def style(self):
        self.setStyleSheet(self.TrelloListHeaderStyle) 

    def __str__(self):
        return "TrelloListHeader|'%s'" % (self.text)
    def __repr__(self):
        return self.__str__()


class TrelloListCards(QtGui.QWidget):
    TrelloListCardsStyle="QLabel { font: bold 15px; }"

    def __init__( self, tlist, cards):
        QtGui.QWidget.__init__(self, tlist)
        self.tlist = tlist

        layout = QtGui.QFormLayout()
        for card in cards:
            print card.getCardInformation()
            layout.addWidget(TrelloCard(tlist, card.id, card.name))
        self.setLayout(layout)
        
        self.style()

    def style(self):
        self.layout().setHorizontalSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setStyleSheet(self.TrelloListCardsStyle) 
        
    def addCard(self):
        pass # TODO: correct position (cf. Trello API)



class WorkThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
  
    def run(self):
        while(True):
            time.sleep(5)
            self.emit(QtCore.SIGNAL('update()'))


def main():    
    apiKey = 'cae2c8a0e8fff08a3031310959cb94c8' # TODO conf file
    userAuthToken = '9bbf9f6e2b89d7c098eca47f2265609ee4c04fb317e6f1da1c2ffd5b0daba448'
    client = Client(apiKey, userAuthToken)

    app = QtGui.QApplication(sys.argv)

    boardId = '52120adfbcec5a8c6a0018a8' # TODO conf file
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
