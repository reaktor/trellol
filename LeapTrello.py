#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys, os, math, time
from collections import deque
from PyQt4 import QtGui, QtCore
from LeapListener import LeapListener

from trolly.client import Client
from trolly.board import Board
from trolly.list import List
from trolly.card import Card
from trolly.member import Member
# from trolly.organisation import Organisation
# from trolly.checklist import Checklist
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
        self.window = QtGui.QWidget();
        hbox = QtGui.QHBoxLayout()
        self.window.setLayout(hbox)

        self.setCentralWidget(self.window)
        hbox.setSpacing(0)
        lists = self.board.getLists()
        for rawlist in lists:            
            cards = rawlist.getCards()
            hbox.addWidget( TrelloList( self, self.client, rawlist.id, rawlist.name, cards ) ) 

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setEnabled(True)
        self.scrollArea.setWidget(self.window)
        self.setCentralWidget(self.scrollArea)

        self.currentCard = None
        self.shadowCard = None

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
        logo_h = config.getint('TrelloBoard', 'logo_height') 
        logo_w = config.getint('TrelloBoard', 'logo_width') 
        logo_x = config.getint('TrelloBoard', 'logo_pos_x')
        logo_y = self.height() - logo_h - config.getint('TrelloBoard', 'logo_pos_x')
        
        self.logo.setGeometry(logo_x, logo_y, logo_w, logo_h)

    def mouseMoveEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mouseMoveEvent(self.currentCard, event) 

    def mousePressEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mousePressEvent(self.currentCard, event)


class TrelloList(QtGui.QWidget):

    def __init__(self, board, client, listId, name, cards):
        QtGui.QWidget.__init__(self, board)
        self.board = board
        self.client = client
        self.id = listId
        self.name = name

        layout = QtGui.QFormLayout()
        self.head = TrelloListHeader(self.name)
        layout.addWidget(self.head)
        self.tail = TrelloListCards(self, cards)
        layout.addWidget(self.tail)
        self.setLayout(layout)

        self.style()
        self.show()
        
        self.setAcceptDrops(True)

    def style(self):
        self.layout().setHorizontalSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)        
            
    def __str__(self):
        return "TrelloList|'%s'" % (self.name)
    def __repr__(self):
        return self.__str__()

    def dragEnterEvent(self, e): 
        e.accept()

    def dragMoveEvent(self, e):
        # HACK: we compute a limit for the end of the card list and 
        #       consider a tail move only below that point
        h = config.getint('TrelloCard', 'height') + 5
        lim = h * self.tail.layout().count()
        if lim < e.pos().y():
            self.tail.addCard(e.source())
            e.accept()
            return
        
    def dropEvent(self, e):        
        self.thread = UpdateThread(e.source(), "MOVE")
        self.thread.start()


class TrelloCard(QtGui.QLabel):

    TrelloCardDeselectStyle = config.get('TrelloCard', 'deselect_style')
    TrelloCardSelectStyle = config.get('TrelloCard', 'select_style')
    TrelloCardDragStyle = config.get('TrelloCard', 'drag_style')
    TrelloCardShadowStyle = config.get('TrelloCard', 'shadow_style')
    TrelloCardWidth = config.getint('TrelloCard', 'width')
    TrelloCardHeight = config.getint('TrelloCard', 'height')

    def __init__(self, tlist, cardId, name):
        QtGui.QLabel.__init__(self, tlist)
        self.id = cardId
        self.name = name
        self.tlist = tlist
        
        self.setMouseTracking(True)
        self.setText(self.name)
        self.setAcceptDrops(True)
        self.isShadow = False

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
        self.isShadow = False
        self.setStyleSheet(self.TrelloCardSelectStyle)

    def deselect(self):
        self.isShadow = False
        self.setStyleSheet(self.TrelloCardDeselectStyle)

    def drag(self): # TODO cf. shadow()
        self.setStyleSheet(self.TrelloCardDragStyle)

    def shadow(self):
        self.isShadow = True
        self.setStyleSheet(self.TrelloCardShadowStyle)

    def getCentroid(self):
        x,y,w,h = self.x(), self.y(), self.width(), self.height()
        return (x + (w/2), y + (h/2))

    def getDistTo(self, x, y):
        thisx, thisy = self.getCentroid()
        dist = math.sqrt( (math.pow(thisx - x, 2) + math.pow(thisy - y, 2)))
        return dist

    def setTrellolist(self, tlist):
        self.tlist = tlist

    def mouseMoveEvent(self, event):

        # select by hover over card
        if (self.tlist.board.currentCard is not self):
            if (self.tlist.board.currentCard is not None):
                self.tlist.board.currentCard.deselect()
            self.tlist.board.currentCard = self
            self.select()

        # start drag on 'mouse' press
        if not event.buttons() == QtCore.Qt.NoButton:

            mimeData = QtCore.QMimeData()

            # pixmap = QtGui.QPixmap.grabWidget(self)  # TODO decide between shadow+dragImg vs. no-mouse
            # self.tlist.board.shadowCard = self
            # self.shadow()

            self.drag()
            drag = QtGui.QDrag(self)
            dragCursor = QtGui.QPixmap(os.getcwd() + config.get('resources', 'null_cursor'))
            drag.setDragCursor(dragCursor, QtCore.Qt.MoveAction)
            drag.setMimeData(mimeData)
            drag.setHotSpot(event.pos())        
            drag.exec_(QtCore.Qt.MoveAction)
            
    def dragEnterEvent(self, e):
        e.accept() # needed for DragMoveEvent

    def dragMoveEvent(self, e): 
        if (self == e.source()): return

        cardUpperHalf = e.pos().y() <= (self.height() / 2)
        temp = deque()
        cardlist = self.tlist.tail
        for i in reversed(range(cardlist.count())):
            if (cardlist.getCardAt(i) == self):
                if cardUpperHalf: temp.append(cardlist.takeCardAt(i))
                temp.append(e.source())
                if not cardUpperHalf: temp.append(cardlist.takeCardAt(i))
                break
            elif (cardlist.getCardAt(i) == e.source()):
                cardlist.removeCard(e.source())
            else:
                temp.append(cardlist.takeCardAt(i))
        
        for i in range(len(temp)): 
            w = temp.pop()
            cardlist.addCard(w)

    def dropEvent(self, e):
        e.source().deselect()        
        self.thread = UpdateThread(e.source(), "MOVE")
        self.thread.start()
            
    def __str__(self):
        return "Card %s %s %s" % (self.id, self.name, self.geometry())

    def __repr__(self):
        return self.__str__()


class TrelloListHeader(QtGui.QLabel):
    TrelloListHeaderStyle = config.get('TrelloListHeader', 'style')
    TrelloCardWidth = config.getint('TrelloCard', 'width')
    TrelloCardHeight = config.getint('TrelloCard', 'height')

    def __init__(self, text):
        QtGui.QLabel.__init__(self)

        self.setText(text)
        self.style()

    def style(self):
        self.setFixedHeight(self.TrelloCardHeight/4)
        self.setFixedWidth(self.TrelloCardWidth)
        self.setStyleSheet(self.TrelloListHeaderStyle) 

    def __str__(self):
        return "TrelloListHeader|'%s'" % (self.text)
    def __repr__(self):
        return self.__str__()
  

class TrelloListCards(QtGui.QWidget):
    TrelloListCardsStyle = config.get('TrelloListCards', 'style')

    def __init__( self, tlist, cards):
        QtGui.QWidget.__init__(self, tlist)
        self.tlist = tlist
        self.setLayout(QtGui.QFormLayout())
        for index,card in enumerate(cards):            
            tc = TrelloCard(tlist, card.id, card.name)
            self.addCard(tc)
 
        self.style()

    def style(self):
        self.setStyleSheet(self.TrelloListCardsStyle) 
        self.layout().setHorizontalSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)        

    def count(self):
        return self.layout().count()

    def getCardAt(self, index):
        return self.layout().itemAt(index).widget()

    def takeCardAt(self, index):
        return self.layout().takeAt(index).widget()

    def removeCard(self, card):
        card.setTrellolist(None)
        card.setParent(None)
        for i in range(self.layout().count()):
            if self.layout().itemAt(i) == card:
                return self.layout().takeAt(i)

        return None

    def addCard(self, card):
        card.setTrellolist(self.tlist)
        self.layout().addWidget(card)


class UpdateThread(QtCore.QThread):

    def __init__(self, card, op):
        QtCore.QThread.__init__(self)
        self.OPS = { 'MOVE' : self.move }

        self.card = card
        self.client = self.card.tlist.board.client
        self.op = self.OPS[op]

    def move(self):
        tcard = Card(self.client, self.card.id)
        queryParams = { 'idList' : self.card.tlist.id, 'pos' : 'bottom' }

        temp = deque()
        cardlist = self.card.tlist.tail        
        for i in reversed(range(cardlist.count())):
            ca = cardlist.getCardAt(i)
            if (ca == self.card):
                Card(self.client, ca.id).updateCard(queryParams)
                break
            else:
                temp.append(ca)

        for i in range(len(temp)): 
            ca = temp.pop()
            Card(self.client, ca.id).updateCard(queryParams)

    def run(self):
        self.op()


def main():    
    apiKey =  config.get('main', 'api_key')
    userAuthToken = config.get('main', 'user_token')
    client = Client(apiKey, userAuthToken)

    app = QtGui.QApplication(sys.argv)

    boardId = config.get('main', 'board_id')
    board = TrelloBoard(client, app, boardId)

    listener = LeapListener()
    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"

if __name__ == "__main__":
    main()
