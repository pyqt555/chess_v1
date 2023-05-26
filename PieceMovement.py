import sys
import copy

# Global Constants
WHITE, BLACK = 'w', 'b'
PAWN, BISHOP, KNIGHT, ROOK, QUEEN, KING = 'p', 'B', 'N', 'R', 'Q', 'K'

class Piece:
    def __init__(self, p, name):
        self.picture = p
        self.name = name
        self.piecelist = []
        self.value = 0


class boardState:
    changed = None
    prevBoard = None
    prevState = None
    enPassant = None
    # Castling
    ws, wl, bs, bl = True, True, True, True
    lastCapture, lastPawnMove = 0, 0
    numPieces = 32

curState = boardState()

# White pieces:
wk = Piece("Pieces/WhiteKing.png", KING)
wq = Piece("Pieces/WhiteQueen.png", QUEEN)
wb = Piece("Pieces/WhiteBishop.png", BISHOP)
wn = Piece("Pieces/WhiteKnight.png", KNIGHT)
wr = Piece("Pieces/WhiteRook.png", ROOK)
wp = Piece("Pieces/WhitePawn.png", PAWN)

whitepieces = [wk, wq, wb, wn, wr, wp]
for y in whitepieces: y.colour = WHITE

# Black pieces:
bk = Piece("Pieces/BlackKing.png", KING)
bq = Piece("Pieces/BlackQueen.png", QUEEN)
bb = Piece("Pieces/BlackBishop.png", BISHOP)
bn = Piece("Pieces/BlackKnight.png", KNIGHT)
br = Piece("Pieces/BlackRook.png", ROOK)
bp = Piece("Pieces/BlackPawn.png", PAWN)

blackpieces = [bk, bq, bb, bn, br, bp]
for y in blackpieces: y.colour = BLACK

# Misc.
allpieces = whitepieces + blackpieces
boardlist = [0] * 70 # Just to be safe
pieceIds = {0: None}

# Set the piece Ids right away
for i in allpieces: pieceIds[id(i)]=i


# Clears the board of all pieces
def emptyboard():
    for i in range(64): boardlist[i] = 0

# Looks up the piece in the pieceIds dictionary
def getPiece(pId):
    return pieceIds[pId]


# Adds the positions of all pieces on the board to their respective objects
def updatepieces():
    for y in allpieces:
        y.piecelist = []
    for num, pieceId in enumerate(boardlist):
        if not(pieceId): continue
        getPiece(pieceId).piecelist.append(num)

def updatepiecesfast(changed):
    for i in changed:
        p = getPiece(i)
        toAdd = [] if changed[i][1]==-1 else [changed[i][1]]
        if changed[i][0]!=-1: p.piecelist.remove(changed[i][0])
        newpiecelist = p.piecelist + toAdd
        p.piecelist = newpiecelist


# Reverts the board to the starting position
def resetboard():
    emptyboard()
    boardlist[4] = id(wk)
    boardlist[3] = id(wq)
    boardlist[2], boardlist[5] = id(wb), id(wb)
    boardlist[1], boardlist[6] = id(wn), id(wn)
    boardlist[0], boardlist[7] = id(wr), id(wr)
    for i in range(8, 16): boardlist[i] = id(wp)
    boardlist[60] = id(bk)
    boardlist[59] = id(bq)
    boardlist[61], boardlist[58] = id(bb), id(bb)
    boardlist[62], boardlist[57] = id(bn), id(bn)
    boardlist[63], boardlist[56] = id(br), id(br)
    for i in range(48, 56): boardlist[i] = id(bp)
    updatepieces()

resetboard()


# Resets the board and initializes some values
def resetgame():
    global curState
    resetboard()
    curState = boardState()


# Converts sqr to a number for ease of calculation (sqr is a string coord)
def coordtonum(sqr):
    return 8 * (int(sqr[1]) - 1) + ord(sqr[0]) - 97


# Converts num back to a coordinate
def numtocoord(num):
    return chr(num%8 + 97) + str((num/8)+1)


# Returns the piece on square num
def pieceatsqr(num):
    if num > 63 or num < 0:
        return None
    s = boardlist[num]
    return getPiece(s)


# Changes the value of the piece on start to end
def ChangeVar(start, end):
    j = pieceatsqr(start)
    boardlist[start] = 0
    boardlist[end] = id(j)


# Checks if a pawn has made it to the eighth/first rank
def pawnPromoted(end):
    s = numtocoord(end)
    pce = pieceatsqr(end)
    if (s[1] == '8' and pce == wp) or (s[1] == '1' and pce == bp):
        return True
    return False


# Moves the piece on start to end
def MovePiece(start, end, update=True):
    j = pieceatsqr(start)
    m = pieceatsqr(end)

    curState.prevState = copy.copy(curState)
    curState.prevBoard = copy.copy(boardlist)

    ChangeVar(start, end)
    toUpdate = {id(j):[start,end]}

    # Move the rook if the king castled
    if j.name == KING and (end - start) == 2:
        ChangeVar(end + 1, start + 1)
        toUpdate[id(pieceatsqr(start+1))]=[end+1,start+1]
    elif j.name == KING and (start - end) == 2:
        ChangeVar(end - 2, start - 1)
        toUpdate[id(pieceatsqr(start-1))]=[end-2,start-1]

    # Turn a promoted pawn into a queen
    if pawnPromoted(end):
        if j.colour == WHITE:
            boardlist[end] = id(wq)
            toUpdate[id(wp)]=[start,-1];toUpdate[id(wq)]=[-1,end]
        if j.colour == BLACK:
            boardlist[end] = id(bq)
            toUpdate[id(bp)]=[start,-1];toUpdate[id(bq)]=[-1,end]

    # Updates fields needed for 50-move-rule
    curState.lastCapture += 1
    curState.lastPawnMove += 1
    if m:
        curState.lastCapture = 0
        curState.numPieces -= 1
        toUpdate[id(m)]=[end,-1]

    curState.enPassant = None
    # Checks if En Passant is valid
    if j.name == PAWN:
        curState.lastPawnMove = 0
        s, e = start, end
        if abs(s-e) == 16:
            if j.colour == BLACK:
                curState.enPassant = e+8
            if j.colour == WHITE:
                curState.enPassant = e-8
        if abs(s-e) == 7 or abs(s-e) == 9:
            if not m:
                if j.colour == WHITE:
                    boardlist[e-8] = 0
                    toUpdate[id(bp)]=[e-8,-1]
                elif j.colour == BLACK:
                    boardlist[e+8] = 0
                    toUpdate[id(wp)]=[e+8,-1]
    if update: 
        updatepiecesfast(toUpdate)
        curState.changed = copy.copy(toUpdate)

    updateCastlingRights()
    return j # return piece on start square (mostly for coords)


# Checks if each side can still castle
def updateCastlingRights():
    if boardlist[4] != id(wk):
        curState.ws, curState.wl = False, False
    if boardlist[60] != id(bk):
        curState.bs, curState.bl = False, False
    if boardlist[0] != id(wr):
        curState.wl = False
    if boardlist[56] != id(br):
        curState.bl = False
    if boardlist[7] != id(wr):
        curState.ws = False
    if boardlist[63] != id(br):
        curState.bs = False


# Undoes the previous move made
def UndoMove(update=True):
    global curState
    global boardlist
    if curState.prevState == None:
        return
    
    boardlist = curState.prevBoard
    if update: 
        x = curState.changed
        for i in x: x[i] = [x[i][1],x[i][0]]
        updatepiecesfast(x)
    curState = curState.prevState

    
#helper
def rookMovement(i):
    p = []
    for x in range(i-8,-1,-8):
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i+8,64,8):
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i-1,i-8,-1):
        if x%8 == 7: break
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i+1,i+8):
        if x%8 == 0: break
        p.append(x)
        if boardlist[x] != 0:
            break
    return p

#helper
def bishopMovement(i):
    p =[]
    for x in range(i-9,-1,-9):
        if x%8 == 7: break
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i+9,64,9):
        if x%8 == 0: break
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i-7,0,-7):
        if x%8 == 0: break
        p.append(x)
        if boardlist[x] != 0:
            break
    for x in range(i+7,64,7):
        if x%8 == 7: break
        p.append(x)
        if boardlist[x] != 0:
            break
    return p

#helper
def kingMovement(sqr, i):
    m, n = sqr[0], sqr[1]
    p = []
    if m != 'a':
        p.append(i - 1)
        if n != '1':
            p.append(i - 9)
        if n != '8':
            p.append(i + 7)
    if m != 'h':
        p.append(i + 1)
        if n != '1':
            p.append(i - 7)
        if n != '8':
            p.append(i + 9)
    if n != '1':
        p.append(i - 8)
    if n != '8':
        p.append(i + 8)
    return p

#helper
def knightMovement(sqr, i):
    m, n = sqr[0], sqr[1]
    p = []
    if m != 'a' and m != 'b':
        if n != '1':
            p.append(i - 10)
        if n != '8':
            p.append(i + 6)
    if n != '1' and n != '2':
        if m != 'a':
            p.append(i - 17)
        if m != 'h':
            p.append(i - 15)
    if n != '7' and n != '8':
        if m != 'a':
            p.append(i + 15)
        if m != 'h':
            p.append(i + 17)
    if m != 'g' and m != 'h':
        if n != '1':
            p.append(i - 6)
        if n != '8':
            p.append(i + 10)
    return p

# Returns a list of squares that are valid moves for the piece on square i
def PieceMovement(i):
    j = pieceatsqr(i)
    sqr = numtocoord(i)
    m, n = sqr[0], sqr[1]
    p = []

    if not j: return p

    # King Movement
    if j.name == KING:
        p = kingMovement(sqr, i)
        # Castling
        if (j.colour == WHITE and curState.ws) or (j.colour == BLACK and curState.bs):
            a, b = pieceatsqr(i + 1), pieceatsqr(i + 2)
            if not a and not b:
                # Cannot castle through check
                if isSafe(i+1, j.colour) and isSafe(i+2, j.colour):
                    p.append(i + 2)
        if (j.colour == WHITE and curState.wl) or (j.colour == BLACK and curState.bl):
            a, b, c = pieceatsqr(i - 1), pieceatsqr(i - 2), pieceatsqr(i - 3)
            if not(a) and not(b) and not(c):
                if isSafe(i-1, j.colour) and isSafe(i-2, j.colour):
                    p.append(i - 2)    

    # Pawn Movement
    elif j.name == PAWN:
        ep = curState.enPassant
        if j.colour == WHITE:
            up1, up2 = i+8, i+16
            xleft, xright = i+7, i+9
            startrank = '2'
        elif j.colour == BLACK:
            up1, up2 = i-8, i-16
            xleft, xright = i-9, i-7
            startrank = '7'
        s = pieceatsqr(up1)
        if not(s):
            p.append(up1)
        if m != 'a':
            z = pieceatsqr(xleft)
            if (z and z.colour != j.colour) or ep == xleft:
                p.append(xleft)
        if m != 'h':
            y = pieceatsqr(xright)
            if (y and y.colour != j.colour) or ep == xright:
                p.append(xright)
        if n == startrank:
            t = pieceatsqr(up2)
            if not(s) and not(t):
                p.append(up2)
        
    # Knight Movement
    elif j.name == KNIGHT:
        p = knightMovement(sqr, i)

    # Rook Movement
    elif j.name == ROOK:
        p = rookMovement(i)

    # Bishop Movement
    elif j.name == BISHOP:
        p = bishopMovement(i)

    # Queen Movement
    elif j.name == QUEEN:
        p = rookMovement(i) + bishopMovement(i)

    def MoveFilterer(x):
        # Make sure we don't have friendly fire
        if boardlist[x] and (pieceatsqr(x)).colour == j.colour:
            return False
        # Cannot castle out of check
        if j.name == KING and abs(x-i) == 2 and isInCheck(j.colour):
            return False
        legalMove = True
        MovePiece(i, x, update=False)
        # Cannot move into check
        if isInCheckMod(j.colour):
           legalMove = False 
        UndoMove(update=False)
        return legalMove

    return filter(MoveFilterer, p)


# Danger Functions
def PawnDanger(i, colour):
    if colour == WHITE:
        if i <= 47 and i % 8 != 7 and boardlist[i+9] == id(bp):
            return True
        if i <= 47 and i % 8 != 0 and boardlist[i+7] == id(bp):
            return True
    elif colour == BLACK:
        if i >= 16 and i % 8 != 0 and boardlist[i-9] == id(wp):
            return True
        if i >= 16 and i % 8 != 7 and boardlist[i-7] == id(wp):
            return True

def KnightDanger(sqr, colour):
    if colour == WHITE:
        knight = id(bn)
    else:
        knight = id(wn)
    for y in knightMovement(numtocoord(sqr), sqr):
        if boardlist[y] == knight:
            return True

def KingDanger(sqr, colour):
    if colour == WHITE:
        king = id(bk)
    else:
        king = id(wk)
    for y in kingMovement(numtocoord(sqr), sqr):
        if boardlist[y] == king:
            return True

def BigPieceDanger(sqr, colour):
    if colour == WHITE:
        rook, bishop, queen = id(br), id(bb), id(bq)
    else:
        rook, bishop, queen = id(wr), id(wb), id(wq)
    for y in rookMovement(sqr):
        if boardlist[y] == rook or boardlist[y] == queen:
            return True
    for y in bishopMovement(sqr):
        if boardlist[y] == bishop or boardlist[y] == queen:
            return True

# Determines whether a move can get you killed
def isSafe(sqr, colour, *exclude):
    if not('P' in exclude) and PawnDanger(sqr, colour):
        return False
    if not('N' in exclude) and KnightDanger(sqr, colour):
        return False
    if not('K' in exclude) and KingDanger(sqr, colour):
        return False
    if not('BIG' in exclude) and BigPieceDanger(sqr, colour):
        return False
    return True


# determines whether the 'colour' king is in check
def isInCheck(colour):
    if colour == WHITE:
        kingsqr = wk.piecelist[0]
    elif colour == BLACK:
        kingsqr = bk.piecelist[0]
    return not(isSafe(kingsqr, colour))


# same as isInCheck except it manually finds kingsqr
def isInCheckMod(colour):
    if colour == WHITE:
        king = id(wk)
    elif colour == BLACK:
        king = id(bk)
    for s in range(64):
        if boardlist[s] == king:
            kingsqr = s
            break
    return not(isSafe(kingsqr, colour))


# determines whether colour is in checkmate, stalemate or neither
def isMated(colour, threshold=32):
    inCheck = isInCheck(colour)
    if not(inCheck) and curState.numPieces > threshold:
        return False

    if colour == WHITE:
        pieces = whitepieces
    elif colour == BLACK:
        pieces = blackpieces
    for y in pieces:
        for i in y.piecelist:
            if len(list(PieceMovement(i))) > 0:
                return False
    if inCheck:
        return 'CHECKMATE'
    return 'STALEMATE'


# Returns the boardState i states ago
def prev(i, state):
    if i == 0 or not(state):
        return None
    if i <= 1:
        return state.prevState
    return prev(i-1, state.prevState)


# Determines whether the current position has been consecutively repeated three times
def isRepitition():
    tempState = prev(3, curState)
    tempState2 = prev(2, tempState)
    if tempState and tempState2:
        if boardlist == tempState.prevBoard and boardlist == tempState2.prevBoard:
            return True
    return False


# Determines whether the game is a draw by insufficient material
def isInsufficient():
    if len(wp.piecelist) > 0 or len(bp.piecelist) > 0:
        return False
    elif len(wq.piecelist) > 0 or len(bq.piecelist) > 0:
        return False
    elif len(wr.piecelist) > 0 or len(br.piecelist) > 0:
        return False
    elif len(wb.piecelist) > 1 or len(bb.piecelist) > 1:
        return False
    elif len(wb.piecelist) > 0 and len(wn.piecelist) > 0:
        return False
    elif len(bb.piecelist) > 0 and len(bn.piecelist) > 0:
        return False
    return True


# Returns true if no capture or pawn move has been made in the last 50 moves
def isDrawByFifty():
    if curState.lastCapture >= 100 and curState.lastPawnMove >= 100:
        return True
    return False


# Checks whether the game is a draw
def isDraw():
    if isInsufficient():
        return "INSUFFICIENT MATERIAL"
    if isRepitition():
        return "DRAW BY REPITITION"
    if isDrawByFifty():
        return "DRAW BY 50 MOVE RULE"
    return False
