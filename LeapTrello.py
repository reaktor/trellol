#!/usr/bin/python                                                                                                      
# -*- coding: utf-8 -*- 

"""
Leap Motion + Trello

A plain Trello view with Leap Motion UI.
"""

import Leap, sys, os, math, time
import ConfigParser, argparse
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

class ScrollEventMixin(object):   

    def mouseMoveEvent(self, event):
        bx, by, w, h = self.board.geometry().getRect()
        x,y = event.globalPos().x(), event.globalPos().y()

        scrollZone = self.config.getint('TrelloBoard', 'scroll_zone_size')
        scrollSpeed = self.config.getint('TrelloBoard', 'scroll_speed')
        def maxi(i): return max(i, scrollSpeed)

        # horizontal scroll
        wDiff = x - bx
        isLeft = wDiff < scrollZone
        isRight =  (w - wDiff) < scrollZone
        sb = self.board.scrollArea.horizontalScrollBar()
        if (isLeft): sb.setValue(sb.value() - maxi(wDiff))
        if (isRight): sb.setValue(sb.value() + maxi(w - wDiff))

        # vertical scroll
        hDiff = y - by
        isTop = hDiff < scrollZone 
        isBottom = (h - hDiff) < scrollZone
        sb = self.board.scrollArea.verticalScrollBar()
        if (isTop): sb.setValue(sb.value() - maxi(hDiff))
        if (isBottom): sb.setValue(sb.value() + maxi((h - hDiff)))

    def dragEnterEvent(self, e): 
        e.accept()
    
    
class TrelloBoard(QtGui.QMainWindow):  

    pointingMultiplier = QtCore.pyqtSignal(int)

    def __init__(self, client, app, boardId, config):
        QtGui.QMainWindow.__init__(self)        

        self.lists = []
        self.app = app
        self.client = client
        self.boardId = boardId
        self.config = config

        self.trelloBoardStyle = self.config.get('TrelloBoard', 'style')
        
        self.board = Board(client, boardId)
        self.screen = QtGui.QDesktopWidget().screenGeometry()
        self.setMouseTracking(True)

        self.updatePointingMultiplier()

        self.style()
        self.show()

    def style(self):           
        self.window = QtGui.QWidget();
        hbox = QtGui.QHBoxLayout()
        self.window.setLayout(hbox)

        self.setCentralWidget(self.window)
        hbox.setSpacing(0)
        lists = self.board.getLists()
        for rawlist in lists:            
            cards = rawlist.getCards()
            hbox.addWidget( TrelloList( self.config, self, self.client, rawlist.id, rawlist.name, cards ) ) 

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setEnabled(True)
        self.scrollArea.setWidget(self.window)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.scrollArea)

        self.currentCard = None
        self.shadowCard = None

        self.setWindowTitle(self.config.get('main', 'title'))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet(self.trelloBoardStyle)        

        self.logo = QtGui.QLabel(self)
        self.logo.setPixmap(QtGui.QPixmap(os.getcwd() + self.config.get('resources', 'trellol_logo_small')))
        
        #self.cursorImg = QtGui.QPixmap(os.getcwd() + self.config.get('resources', 'ball_cursor'))
        self.cursorImg = QtGui.QPixmap(os.getcwd() + self.config.get('resources', 'null_cursor'))
        self.setCursor(QtGui.QCursor(self.cursorImg, -1, -1))
        
        self.center()

    def center(self):
        mainposx = self.config.getint('main', 'pos_x')
        mainposy = self.config.getint('main', 'pos_y')
        mainwidth = self.config.getint('main', 'width')
        mainheight = self.config.getint('main', 'height')

        self.setGeometry(mainposx, mainposy, mainwidth, mainheight)        
        size = self.geometry()
        self.move((self.screen.width() - size.width()) / 2, (self.screen.height() - size.height()) / 2)
      
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()
        elif key == QtCore.Qt.Key_F:
            if self.windowState() & QtCore.Qt.WindowFullScreen:
                self.showNormal()
            else:
                self.showFullScreen()

        self.updatePointingMultiplier()
        return QtGui.QWidget.keyPressEvent(self, event)

    def resizeEvent(self, e):
        logo_h = self.config.getint('TrelloBoard', 'logo_height') 
        logo_w = self.config.getint('TrelloBoard', 'logo_width') 
        logo_x = self.config.getint('TrelloBoard', 'logo_pos_x')
        logo_y = self.height() - logo_h - self.config.getint('TrelloBoard', 'logo_pos_x')
        
        self.logo.setGeometry(logo_x, logo_y, logo_w, logo_h)

    def mouseMoveEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mouseMoveEvent(self.currentCard, event) 

    def mousePressEvent(self, event):
        if (self.currentCard is not None):
            TrelloCard.mousePressEvent(self.currentCard, event)

    def updatePointingMultiplier(self):
        diagonal = math.sqrt( (math.pow(self.width(), 2) + math.pow(self.height(), 2)))
        multiplier = max(min(diagonal / 100, 20), 5)
        self.pointingMultiplier.emit(multiplier)

class TrelloList(QtGui.QWidget, ScrollEventMixin):

    def __init__(self, config, board, client, listId, name, cards):
        QtGui.QWidget.__init__(self, board)
        self.config = config
        self.board = board
        self.client = client
        self.id = listId
        self.name = name        

        layout = QtGui.QFormLayout()
        self.head = TrelloListHeader(config, self, self.name)
        layout.addWidget(self.head)
        self.tail = TrelloListCards(config, self, cards)
        layout.addWidget(self.tail)
        self.setLayout(layout)

        self.style()
        self.show()
        
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

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
        h = self.config.getint('TrelloCard', 'height') + 5
        lim = h * self.tail.layout().count()
        if lim < e.pos().y():
            self.tail.addCard(e.source())
            e.accept()
            return

        print "dragMoveEvent TList"
        TrelloCard.dragMoveEvent(self.board.currentCard, e)
        
    def dropEvent(self, e):        
        self.thread = UpdateThread(e.source(), "MOVE")
        self.thread.start()

    def mousePressEvent(self, event):
        if (self.board.currentCard is not None):
            TrelloCard.mouseMoveEvent(self.board.currentCard, event)


class TrelloCard(QtGui.QLabel, ScrollEventMixin):

    def __init__(self, config, tlist, cardId, name):
        QtGui.QLabel.__init__(self, tlist)
        self.config = config
        self.id = cardId
        self.name = name
        self.tlist = tlist
        self.board = tlist.board        

        self.trelloCardDeselectStyle = self.config.get('TrelloCard', 'deselect_style')
        self.trelloCardSelectStyle = self.config.get('TrelloCard', 'select_style')
        self.trelloCardDragStyle = self.config.get('TrelloCard', 'drag_style')
        self.trelloCardShadowStyle = self.config.get('TrelloCard', 'shadow_style')
        self.trelloCardMemberStyle = config.get('TrelloCard', 'member_style')
        self.trelloCardMemberHeight = config.getint('TrelloCard', 'member_height')
        self.trelloCardMemberBorder = config.getint('TrelloCard', 'member_border')
        self.trelloCardWidth = self.config.getint('TrelloCard', 'width')
        self.trelloCardHeight = self.config.getint('TrelloCard', 'height')
        
        self.setMouseTracking(True)
        self.setText(self.name)
        self.addMembers(self.id)
        self.setAcceptDrops(True)
        self.isShadow = False

        self.style()

    def style(self):
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.deselect()
        self.setFixedHeight(self.trelloCardHeight)
        self.setFixedWidth(self.trelloCardWidth)
        
    def select(self):
        self.isShadow = False
        self.setStyleSheet(self.trelloCardSelectStyle)

    def deselect(self):
        self.isShadow = False
        self.setStyleSheet(self.trelloCardDeselectStyle)

    def drag(self): # TODO cf. shadow()
        self.setStyleSheet(self.trelloCardDragStyle)

    def shadow(self):
        self.isShadow = True
        self.setStyleSheet(self.trelloCardShadowStyle)

    def getCentroid(self):
        x,y,w,h = self.x(), self.y(), self.width(), self.height()
        return (x + (w/2), y + (h/2))

    def getDistTo(self, x, y):
        thisx, thisy = self.getCentroid()
        dist = math.sqrt( (math.pow(thisx - x, 2) + math.pow(thisy - y, 2)))
        return dist

    def addMembers(self, cardId):
        members = Card(self.tlist.board.client, cardId).getCardInformation()['idMembers']
        
        for i, member in enumerate(members):
            initials = Member(self.tlist.board.client, member).getMemberInformation()['initials']
            self.addMemberLabel(
                self, 
                initials, 
                self.TrelloCardMemberBorder + 25 * i, 
                self.TrelloCardHeight - self.TrelloCardMemberHeight -  self.TrelloCardMemberBorder
            )
            
    def addMemberLabel(self, parent, text, x, y):
        label = QtGui.QLabel(text, parent)
        label.setFixedHeight(self.TrelloCardMemberHeight)
        label.setStyleSheet(self.TrelloCardMemberStyle)
        label.move(x, y)

    def setTrellolist(self, tlist):
        self.tlist = tlist

    def mouseMoveEvent(self, event):
        ScrollEventMixin.mouseMoveEvent(self, event)

        # select by hover over card
        if (self.tlist.board.currentCard is not self):
            if (self.tlist.board.currentCard is not None):
                self.tlist.board.currentCard.deselect()
            self.tlist.board.currentCard = self
            self.select()

        # start drag on 'mouse' press
        if not (event.buttons() == QtCore.Qt.NoButton):
            mimeData = QtCore.QMimeData()

            # pixmap = QtGui.QPixmap.grabWidget(self)  # TODO decide between shadow+dragImg vs. no-mouse
            # self.tlist.board.shadowCard = self
            # self.shadow()

            self.drag()
            drag = QtGui.QDrag(self)
            dragCursor = QtGui.QPixmap(os.getcwd() + self.config.get('resources', 'null_cursor'))
            drag.setDragCursor(dragCursor, QtCore.Qt.MoveAction)
            drag.setMimeData(mimeData)
            drag.setHotSpot(event.pos())        
            drag.exec_(QtCore.Qt.MoveAction)
            
    def dragEnterEvent(self, e):
        e.accept() # needed for DragMoveEvent

    def dragMoveEvent(self, e): 
        # # TODO: scroll while dragging; a good start below
        # glob = QtCore.QPoint(self.board.x() + e.pos().x(), self.board.y() + e.pos().y())
        # ev = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, e.pos(), glob, 
        #                        QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)     
        # print ev.pos(), ev.globalPos()
        # ScrollEventMixin.mouseMoveEvent(self, ev)    

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


class TrelloListHeader(QtGui.QLabel, ScrollEventMixin):

    def __init__(self, config, tlist, text):
        QtGui.QLabel.__init__(self)

        self.config = config    
        self.board = tlist.board
        self.setText(text)

        self.trelloListHeaderStyle = self.config.get('TrelloListHeader', 'style')
        self.trelloCardWidth = self.config.getint('TrelloCard', 'width')
        self.trelloCardHeight = self.config.getint('TrelloCard', 'height')

        self.style()

        self.setMouseTracking(True)

    def style(self):
        self.setFixedHeight(self.trelloCardHeight / 4)
        self.setFixedWidth(self.trelloCardWidth)
        self.setStyleSheet(self.trelloListHeaderStyle) 

    def __str__(self):
        return "TrelloListHeader|'%s'" % (self.text())
    def __repr__(self):
        return self.__str__()
  
class TrelloListCards(QtGui.QWidget, ScrollEventMixin):

    def __init__( self, config, tlist, cards):
        QtGui.QWidget.__init__(self, tlist)

        self.config = config
        self.tlist = tlist
        self.board = tlist.board        

        self.trelloListCardsStyle = self.config.get('TrelloListCards', 'style')

        self.setLayout(QtGui.QFormLayout())
        for index,card in enumerate(cards):            
            tc = TrelloCard(config, tlist, card.id, card.name)
            self.addCard(tc)

        self.setMouseTracking(True)
 
        self.style()

    def style(self):
        self.setStyleSheet(self.trelloListCardsStyle) 
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

    def __str__(self):
        return "TrelloListCards| %d card(s)" % (self.layout().count())
    def __repr__(self):
        return self.__str__()

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
    parser = argparse.ArgumentParser(description="Leap Motion Trello")
    parser.add_argument("-c", "--configFile", type=str, default="default.cfg",
                        help="Self.Configuration file is currently the only way to customize LeapMotionTrello.")    
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(args.configFile)
       
    apiKey =  config.get('main', 'api_key')
    userAuthToken = config.get('main', 'user_token')
    client = Client(apiKey, userAuthToken)
    
    app = QtGui.QApplication(sys.argv)

    boardId = config.get('main', 'board_id')
    board = TrelloBoard(client, app, boardId, config)

    listener = LeapListener()
    board.pointingMultiplier[int].connect(listener.setPointingMultiplier)

    controller = Leap.Controller()
    controller.add_listener(listener)

    app.exec_() # blocking

    controller.remove_listener(listener)
    print "Finished"


if __name__ == "__main__":
    main()
