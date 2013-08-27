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
#from trolly.member import Member
# from trolly import ResourceUnavailable

import ConfigParser
config = ConfigParser.ConfigParser()
config.read('conf')
    
class TrelloBoard(QtGui.QMainWindow):  
    TrelloBoardStyle=config.get('TrelloBoard', 'style')

    def __init__(self, client, app, boardId):
        QtGui.QMainWindow.__init__(self)

        self.lists = []
        self.app = app
        self.client = client
        self.boardId = boardId

        self.board = Board(client, boardId)
        self.setMouseTracking(True)
        self.render()
        self.style()
        self.show()

    def style(self):           
        self.setWindowTitle(config.get('main', 'title'))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet(self.TrelloBoardStyle)        

        self.logo = QtGui.QLabel(self)
        self.logo.setPixmap(QtGui.QPixmap(os.getcwd() + config.get('resources', 'trellol_logo_small')))
        
        #self.cursorImg = QtGui.QPixmap(os.getcwd() + config.get('resources', 'ball_cursor'))
        self.cursorImg = QtGui.QPixmap(os.getcwd() + config.get('resources', 'null_cursor'))
        self.setCursor(QtGui.QCursor(self.cursorImg, -1, -1))
        
        self.center()

    def center(self):
        mainposx = config.getint('main', 'pos_x')
        mainposy = config.getint('main', 'pos_y')
        mainwidth = config.getint('main', 'width')
        mainheight = config.getint('main', 'height')

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

        self.window = QtGui.QWidget()
        self.window.setLayout(hbox)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setEnabled(True)
        self.scrollArea.setWidget(self.window)
        self.setCentralWidget(self.scrollArea)
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
        self.logo.setGeometry(
            config.getint('TrelloBoard', 'logo_pos_x'), 
            config.getint('main', 'height') - config.getint('TrelloBoard', 'logo_height') - config.getint('TrelloBoard', 'logo_pos_x'), 
            config.getint('TrelloBoard', 'logo_width'), 
            config.getint('TrelloBoard', 'logo_height')
        )

    def mouseMoveEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mouseMoveEvent(self.currentCard, event) 

    def mousePressEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mousePressEvent(self.currentCard, event)


class TrelloList(QtGui.QWidget):
    def __init__(self, board, client, listId, name, cards):
        QtGui.QWidget.__init__(self)
        self.board = board
        self.client = client
        self.id = listId
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
        self.layout().addWidget(self.board.currentCard)
        e.source().drag()
        e.accept()

    def dropEvent(self, e):
        # TODO Make async
        Card(self.client, e.source().id).updateCard({ 'idList' : self.id})
        # TODO: Prettify the drop event
        # position = e.pos()        
        # e.source().move(position - e.source().rect().center())
        e.source().select()
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()


class TrelloCard(QtGui.QLabel):

    TrelloCardDeselectStyle=config.get('TrelloCard', 'deselect_style')
    TrelloCardSelectStyle=config.get('TrelloCard', 'select_style')
    TrelloCardDragStyle=config.get('TrelloCard', 'drag_style')
    TrelloCardWidth = config.getint('TrelloCard', 'width')
    TrelloCardHeight = config.getint('TrelloCard', 'height')

    def __init__(self, tlist, card):
        QtGui.QLabel.__init__(self)
        self.id = card.id
        self.name = card.name
        self.tlist = tlist
        
        self.setMouseTracking(True)
        self.setText(self.name)
        self.style()
        #idMembers = card.getCardInformation()['idMembers']
        #for idMember in idMembers:
        #    print Member(self.tlist.board.client, idMember).getMemberInformation()['fullName']

    def style(self):
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.deselect()
        self.setFixedHeight(self.TrelloCardHeight)
        self.setFixedWidth(self.TrelloCardWidth)
        
    def select(self):
        self.setStyleSheet(self.TrelloCardSelectStyle)

    def deselect(self):
        self.setStyleSheet(self.TrelloCardDeselectStyle)

    def drag(self):
        self.setStyleSheet(self.TrelloCardDragStyle)

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
            
            drag = QtGui.QDrag(self)
            dragCursor = QtGui.QPixmap(os.getcwd() + config.get('resources', 'null_cursor'))
            drag.setDragCursor(dragCursor, QtCore.Qt.MoveAction)
            drag.setMimeData(mimeData)
            drag.setHotSpot(event.pos())        
            drag.exec_(QtCore.Qt.MoveAction)

    def mousePressEvent(self, event):
        QtGui.QLabel.mousePressEvent(self, event)

    def __str__(self):
        return "Card @  %s" % (self.geometry())


class TrelloListHeader(QtGui.QLabel):
    TrelloListHeaderStyle=config.get('TrelloListHeader', 'style')

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
    TrelloListCardsStyle=config.get('TrelloListCards', 'style')

    def __init__( self, tlist, cards):
        QtGui.QWidget.__init__(self, tlist)
        self.tlist = tlist

        layout = QtGui.QFormLayout()
        for card in cards:
            layout.addWidget(TrelloCard(tlist, card))
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
    apiKey =  config.get('main', 'api_key')
    userAuthToken = config.get('main', 'user_token')
    client = Client(apiKey, userAuthToken)

    app = QtGui.QApplication(sys.argv)

    boardId = config.get('main', 'board_id')
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
