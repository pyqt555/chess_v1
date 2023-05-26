import pygame
import sys
import ChessEngine
import PieceMovement as pm
from PieceMovement import WHITE, BLACK
import random
import time
import numpy as np


backcolour = (255, 255, 255)
boardcolour = (0, 0, 0)
lightblue = (255, 255, 255)
blue = (0, 0, 128)
green = (0, 255, 0)
brown = (50, 50, 50)
purple = (138, 6, 255)

marginsize = 30
screenwidth = 1024 # 640 for a smaller screen
screenheight = 1024 # 480 for a smaller screen

xcorner = max(0, screenwidth - screenheight) / 2 + marginsize
ycorner = max(0, screenheight - screenwidth) / 2 + marginsize
boardsize = min(screenheight, screenwidth) - 2 * marginsize
squaresize = boardsize / 8

buttonWidth, buttonHeight = 75, 12
buttonx = screenwidth / 2 - buttonWidth / 2
buttony = screenheight - 3*(marginsize / 4)
undox, flipx = buttonx + 100, buttonx - 100

pygame.init()
screen = pygame.display.set_mode((screenwidth, screenheight))
MessageFont = pygame.font.SysFont("comic sans", 18)
ButtonFont = pygame.font.SysFont("comic sans", 18)


# helper to obtain file and rank
def fileAndRank(sqr):
    if mainState.FLIP:
        return 7 - sqr%8, sqr//8
    else:
        return sqr%8, 7 - sqr//8


def checkType(event):
    # Check for quit
    if event.type == pygame.QUIT:
        pygame.quit(); sys.exit();
    # Reset the game if 'new game' selected
    if event.type == pygame.MOUSEBUTTONUP:
        mousex, mousey = event.pos
        if buttonx < mousex < buttonx + buttonWidth and buttony < mousey < buttony + buttonHeight:
            resetState()
            return True
        elif undox < mousex < undox + buttonWidth and buttony < mousey < buttony + buttonHeight:
            UndoStuff()
            return True
        elif flipx < mousex < flipx + buttonWidth and buttony < mousey < buttony + buttonHeight:
            mainState.FLIP = not(mainState.FLIP)
            drawStuff()
            return True


# Draws a message above the board
def displayMessage(message, xcoord):
    message = MessageFont.render(message, 1, blue)
    screen.blit(message, (xcoord, marginsize /2))
    pygame.display.update()
    mainState.END = True


# Load an image and set it to the specified size
def loadAndTransform(image, size):
    loadedImage = pygame.image.load(image)
    return pygame.transform.smoothscale(loadedImage, (size, size))


# Adds dead pieces to their respective lists
def checkForDead(start, end):
    piece = pm.pieceatsqr(end)
    if piece:
        if piece.colour == WHITE:
            mainState.deadWhite.append(piece)
        elif piece.colour == BLACK:
            mainState.deadBlack.append(piece)
    elif abs(start-end) == 7 or abs(start-end) == 9:
        if pm.pieceatsqr(start) == pm.wp:
            mainState.deadBlack.append(pm.bp)
        elif pm.pieceatsqr(start) == pm.bp:
            mainState.deadWhite.append(pm.wp)


# Brings back dead pieces that should not be dead
def reviveDead():
     for deadList in mainState.deadWhite, mainState.deadBlack:
        x = len(deadList)
        if x > 0:
            p = deadList[x-1] # Most recently added piece
            c, d =  deadList.count(p), len(p.piecelist)
            if p.name == pm.PAWN and c+d != 8:
                deadList.pop()
            elif (p.name == pm.BISHOP or p.name == pm.ROOK
                  or p.name == pm.KNIGHT) and c+d != 2:
                deadList.pop()
            elif p.name == pm.QUEEN and c+d != 1:
                deadList.pop()


# Draws the board to the screen
def drawBoard():
    x, y = xcorner, ycorner
    k, size = squaresize, boardsize
    pygame.draw.rect(screen, boardcolour, (x, y, size, size), 3)
    for sqr in range(64):
        f, r = fileAndRank(sqr)
        sx = x + f*k + 2 # Add 2 to centre the board
        sy = y + r*k + 2
        if (r%2+f)%2!=0:
            pygame.draw.rect(screen, brown, (sx, sy, k, k))
        else:
            pygame.draw.rect(screen, lightblue, (sx, sy, k, k))        


# Draws the pieces to the screen
def drawPieces():
    k = squaresize
    for p in pm.allpieces:
        pieceImage = loadAndTransform(p.picture, k)
        for sqr in p.piecelist:
            f, r = fileAndRank(sqr)
            screen.blit(pieceImage, (xcorner + f*k, ycorner + r*k))
    pygame.display.update()


# Draws the buttons below the board
def drawButtons():
    def buttonHelper(xcoord, text):
        x, y = xcoord, buttony
        #pygame.draw.rect(screen, boardcolour, (x, y, buttonWidth, buttonHeight), 2)
        messagex = x + 75//2 - ((len(text) * 75//11) / 2) # Magic to centre text
        screen.blit(ButtonFont.render(text, 1, blue), (messagex , y+3))
    buttonHelper(buttonx, "NEW GAME")
    buttonHelper(undox, "UNDO ")
    buttonHelper(flipx, "FLIP")
    

# Highlights the specified square
def drawHighlight(sqr):
    f, r = fileAndRank(sqr)
    x = xcorner + f * squaresize + 2
    y = ycorner + r * squaresize + 2
    pygame.draw.rect(screen, purple, (x, y, squaresize, squaresize))


# Draws pieces that died on the battlefield
def drawDead():
    size = (xcorner - 4) / 4
    def drawDeadHelper(i, picture, startx, starty, u):
        pieceImage = loadAndTransform(picture, size)
        k = i / 4
        x, y = startx + ((i-(4*k))*size), starty + k*size*u
        screen.blit(pieceImage, (x, y))
    whitex, whitey = 4, marginsize
    blackx, blacky = xcorner + boardsize + 4, boardsize - marginsize
    for i, p in enumerate(mainState.deadWhite):
        drawDeadHelper(i, p.picture, whitex, whitey, 1)
    for i, p in enumerate(mainState.deadBlack):
        drawDeadHelper(i, p.picture, blackx, blacky, -1)
    

# Returns square clicked (as a number) or -1 if mouse was off board
def squareClicked(mousex, mousey):
    x = mousex - xcorner
    y = mousey - ycorner
    k, size = squaresize, boardsize
    if x>0 and x<size and y>0 and y<size:
        fil = x // k
        rank = y // k
        sqr = 8*(7-rank) + fil
        if mainState.FLIP:
            sqr = 63 - sqr
        return int(np.round(sqr,0))
    return -1


# Draws a circle for each valid move of the piece on sqr
def drawMoves(sqr):
    for s in pm.PieceMovement(sqr):
        f, r = fileAndRank(s)
        k, size = squaresize, boardsize
        x = (xcorner + k*f + k/2) // 1
        y = (ycorner + k*r + k/2) // 1
        pygame.draw.circle(screen, green, (x, y), k//4, 0)
        pygame.display.update()


# Redraws the board and pieces
def drawStuff(sqr=-1):
    screen.fill(backcolour)
    drawButtons()
    drawBoard()
    if sqr != -1: drawHighlight(sqr)
    drawDead()
    drawPieces()


# A class used for resetting the game
class GameState:
    def __init__(self):
        self.movenumber = 0
        self.turn = WHITE
        self.randmove = random.random()
        self.deadBlack = []
        self.deadWhite = []
        self.FLIP = False
        self.END = False

mainState = GameState()

def resetState():
    global mainState
    mainState = GameState()
    pm.resetgame()
    drawStuff()


# Undoes a move !!
def UndoStuff():
    if mainState.END: mainState.END = False
    pm.UndoMove()
    pm.UndoMove()
    reviveDead()
    drawStuff()
    if mainState.movenumber == 1:
        mainState.turn = WHITE
    if mainState.movenumber != 0:
        mainState.movenumber -= 1


# Switches turn and increases move number
def switchTurn(turn):
    if turn == WHITE:
        mainState.turn = BLACK
        mainState.movenumber += 1
    elif turn == BLACK:
        mainState.turn = WHITE


# Makes a move for the computer
def DoCompTurn(turn):
    if mainState.END: return
    if mainState.movenumber <= 5:
        start, end = ChessEngine.OpeningMoves(turn, mainState.movenumber, mainState.randmove)
    else:
        mv = ChessEngine.FindBest(turn)
        start, end = mv.movestart, mv.moveend
    checkForDead(start, end)
    pm.MovePiece(start, end)
    drawStuff(end)
    switchTurn(turn)


# Moves a piece selected by the player
def DoPlayerTurn(turn):
    temp = -1
    while (True):
        for event in pygame.event.get():
            if checkType(event):
                return
            if event.type == pygame.MOUSEBUTTONUP:
                mousex, mousey = event.pos
                msqr = squareClicked(mousex, mousey)
                if msqr != -1:

                    # Moves a piece if one was selected
                    if temp != -1:
                        for s in pm.PieceMovement(temp):
                            if msqr == s:
                                checkForDead(temp, msqr)
                                pm.MovePiece(temp, msqr)
                                drawStuff()
                                switchTurn(turn)
                                return
                        drawStuff()
                        temp = -1

                    # Displays valid moves
                    else:
                        if turn == WHITE:
                            folder = pm.whitepieces
                        elif turn == BLACK:
                            folder = pm.blackpieces
                        for piece in folder:
                            
                            if id(piece) == pm.boardlist[int(np.round(msqr,0))]:
                                drawMoves(msqr)
                                temp = msqr
                                break

                                             
def main():
    # Initialize things
    pygame.display.set_caption('Can you beat Shallow Blue in chess?')
    pm.updateCastlingRights()
    drawStuff()

    # Main game loop:
    while (True):
        for event in pygame.event.get():
            checkType(event)
        # Checks for mate
        if not mainState.END:
            mate_status = pm.isMated(mainState.turn)
        if mate_status:
            displayMessage(mate_status + "!", screenwidth / 2 - marginsize)
            continue
        # Checks for draw
        draw_status = pm.isDraw() 
        if draw_status:
            displayMessage(draw_status, screenwidth / 2 - 2*marginsize)

        elif mainState.turn == WHITE:
            DoPlayerTurn(mainState.turn)

        elif mainState.turn == BLACK:
            DoCompTurn(mainState.turn)

# Main program
if __name__ == '__main__':
    main()
