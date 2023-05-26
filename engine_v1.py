import sys
import PieceMovement as pm
from PieceMovement import *
from functools import partial
import cProfile
import time

# Global Constants:
Pval = 1
Nval = 3
Bval = 3
Rval = 5
Qval = 9
Kval = 100

mateThreshold = Kval - 2*Qval - 2*Pval
DEPTH=4  # Change these numbers to change difficulty
maxWidth = 10          #
NOISY_LOGGING = True
current_time_millis = lambda: int(round(time.time() * 1000))

move_num = 0

# Assign a value to each piece
for y in allpieces:
    if y.name == PAWN:
        y.value = Pval
    elif y.name == KNIGHT:
        y.value = Nval
    elif y.name == BISHOP:
        y.value = Bval
    elif y.name == ROOK:
        y.value = Rval
    elif y.name == QUEEN:
        y.value = Qval


# Gives a numerical value for how good colour's position is
def EvaluatePosition(colour):
    evalu = 0.01
    BL = pm.boardlist

    # Check for draw
    if isDraw():
        return 0

    # Calculate material imbalances
    for y in whitepieces:
        evalu += y.value * len(y.piecelist)
    for y in blackpieces:
        evalu -= y.value * len(y.piecelist)

    if colour == BLACK:
        evalu *= -1
        opp = WHITE
    else:
        opp = BLACK

    if isInCheck(opp):
        if isMated(opp):
            return Kval

    if move_num <=10:
        evalu += EvaluateOpening(colour)
    elif isEndgame():
        evalu += EvaluateEndgame(colour)
    else:
        evalu += EvaluateMiddleGame(colour)

    return evalu


class Position:
    evaluation = 0
    movestart = 0
    moveend = 0
    mateIn = 0
    #plies = 0
    coords = ''
    

# Returns the "best" move for colour
def FindBest(colour, depth=DEPTH, width=maxWidth, first=True):
    
    time0 = current_time_millis()
    if width <= 0: width = 1
    
    if colour == WHITE:
        pieces = whitepieces
        opp = BLACK
    elif colour == BLACK:
        pieces = blackpieces
        opp = WHITE

    topMoves = []
    e = lambda pos: pos.evaluation


    ##rec_step_0
    if depth==0:
        last_top=[]
        for p in pieces:
            for start in p.piecelist:
                for end in PieceMovement(start):
                    cur = Position()
                    cur.movestart, cur.moveend = start, end

                    i = pieceatsqr(end) # Executes before piece is moved

                    MovePiece(start, end)
                    cur.evaluation = EvaluatePosition(colour)
                    UndoMove()

                    if len(topMoves) < width:
                        last_top.append(cur)
                        last_top.sort(key=e)
                    elif cur.evaluation > last_top[0].evaluation:
                        last_top[0] = cur
                        last_top.sort(key=e)
                    if cur.evaluation >= mateThreshold:
                        cur.mateIn = 1
                        #cur.plies = 0
                        return cur
        return last_top[0]
    ##end_rec_step_0
    for p in pieces:
        for start in p.piecelist:
            for end in PieceMovement(start):
                cur = Position()
                cur.movestart, cur.moveend = start, end

                i = pieceatsqr(end) # Executes before piece is moved

                MovePiece(start, end)
                cur.evaluation = EvaluatePosition(colour)
                UndoMove()

                if len(topMoves) < width:
                    topMoves.append(cur)
                    topMoves.sort(key=e)
                elif cur.evaluation > topMoves[0].evaluation:
                    topMoves[0] = cur
                    topMoves.sort(key=e)

                # Return right away if a mate is found
                if cur.evaluation >= mateThreshold:
                    cur.mateIn = 1
                    #cur.plies = 0
                    return cur

    if len(topMoves) == 0:
        if isInCheck(colour):
            return 'C'
        else:
            return 'S'

    # We assign plies equally among the list of moves
    #extra = plies % len(topMoves)
    #assignedPlies = plies / len(topMoves) + (extra>0)
    for pos in topMoves:
        #extra -= 1;
        #if extra == 0: assignedPlies -= 1
        #if assignedPlies <= 0: break
        if pos.evaluation == 0: continue

        # Actually move the Piece
        startPiece = MovePiece(pos.movestart, pos.moveend)
        oppTop = FindBest(opp, depth-1, width-1, False)

        if oppTop == 'C':
            pos.mateIn = 1
            pos.evaluation = Kval
        elif oppTop == 'S':
            pos.evaluation = 0
        else:
            if oppTop.mateIn: pos.mateIn = oppTop.mateIn + 1
            pos.evaluation = (-1) * oppTop.evaluation
            
        UndoMove()

        capture = (True if pieceatsqr(pos.moveend) else False)
        pos.coords = toCoords(pos.movestart,pos.moveend,startPiece.name,capture) +\
            "," + oppTop.coords

        if first:
            if pos.mateIn:
                printval = "Mate in " + str(pos.mateIn // 2)
            else:
                printval = pos.evaluation
            print (pos.coords, "(", printval, ")")

        # TODO: Add any extra plies to the assigned plies
        # assignedPlies += (assignedPlies - oppTop.plies) / len(topMoves)

    best = max(topMoves, key=e)

    if first:
        if NOISY_LOGGING:
            print ("Time:", current_time_millis() - time0)
            print ("---------")
        if best.evaluation <= -(mateThreshold) and width <= maxWidth:
            return FindBest(colour, depth+1, maxWidth*2, False)

    return best


# returns True if kingpos has the opposition against the enemy king
def hasOpposition(kingpos, opp_pos):
    a, b = kingpos, opp_pos
    if abs(a-b) == 16 or (a/8 == b/8 and abs(a-b) == 2):
        return True
    elif abs(a-b) == 32 or (a/8 == b/8 and abs(a-b) == 4):
        return True
    elif abs(a-b) == 48 or (a/8 == b/8 and abs(a-b) == 6):
        return True
    # Check opposition for corners
    elif (b==0 or b==63) and abs(a-b) == 17:
          return True
    elif (b==7 or b==56) and abs(a-b) == 15:
          return True
    return False


# Returns true if the position seems to be an endgame
def isEndgame():
    if len(wp.piecelist) == 0 or len(bp.piecelist) == 0:
        return True
    elif len(wq.piecelist) == 0 and len(bq.piecelist) == 0:
        return True
    elif len(wb.piecelist) == 0 and len(wn.piecelist) == 0:
        if len(bb.piecelist) == 0 and len(bn.piecelist) == 0:
            return True
    return False


def EvaluateOpening(colour):
    evalu = 0

    hs = wk.piecelist[0]
    ls = bk.piecelist[0]
    # Add incentives for castling
    if hs == 2 or hs == 6:
        evalu += 0.07
    # Discourage useless king marches
    elif not(curState.wl or curState.ws):
        evalu -= 0.03
    if ls == 57 or ls == 62:
        evalu -= 0.07
    elif not(curState.bl or curState.bs):
        evalu += 0.03

    if colour == BLACK:
        evalu *= -1
        
    return evalu



def EvaluateMiddleGame(colour):
    evalu = 0

    for y in wp.piecelist:
        # Add incentives for centred pawns
        if y == 27 or y == 28:
            evalu += 0.1#4
        # Add incentives for making use of outposts for knights
        if y > 24 and y < 48:
            f = y % 8
            if pm.boardlist[y+9] == id(wn) or pm.boardlist[y+7] == id(wn):
                if f > 0 and f < 7:
                    evalu += 0.035
        # Doubled pawns are BAD
        if y < 56 and pm.boardlist[y + 8] == id(wp):
            evalu -= 0.05

    for y in bp.piecelist:
        if y == 35 or y == 36:
            evalu -= 0.1#4
        if y > 24 and y < 48:
            f = y % 8
            if pm.boardlist[y-9] == id(bn) or pm.boardlist[y-7] == id(bn):
                if f > 0 and f < 7:
                    evalu -= 0.035
        if y < 56 and pm.boardlist[y + 8] == id(bp):
            evalu += 0.05

    for y in wn.piecelist:
        # Add incentives for development
        if y == 18 or y == 21:
            evalu += 0.03
    for y in bn.piecelist:
        if y == 42 or y == 45:
            evalu -= 0.03

    for y in wb.piecelist:
        # Fianchetto
        if y == 9 or y == 14:
            evalu += 0.035
    for y in bb.piecelist:
        if y == 49 or y == 54:
            evalu -= 0.035

    for y in wr.piecelist:
        r,f = divmod(y,8)
        # Centralize rooks
        if f == 3 or f == 4:
            evalu += 0.025
        # Rooks on open/semi-open files
        for x in [f+8, f+16, f+24, f+32, f+40, f+48]:
            if pm.boardlist[x] == id(wp):
                evalu -= 0.05
                break
        # Rook on seventh rank is good
        if r == 6:
            evalu += 0.035
    for y in br.piecelist:
        r,f = divmod(y,8)
        if f == 3 or f == 4:
            evalu -= 0.025
        for x in [f+8, f+16, f+24, f+32, f+40, f+48]:
            if pm.boardlist[x] == id(bp):
                evalu += 0.05
                break
        # Rook on second rank is good
        if r == 1:
            evalu -= 0.035

    if colour == BLACK:
        evalu *= -1
        
    return evalu


def EvaluateEndgame(colour):
    evalu = 0
    BL = pm.boardlist

    for p in wp.piecelist:
        # Make sure pawns are safe
        if not(isSafe(p, WHITE)) and isSafe(p, BLACK):
            evalu -= 0.4
        # Passed pawns are GREAT
        #TODO: improve alorithm for determining value of passed pawns
        if p >= 24 and BL[p+8] == 0 and BL[p+9] != id(bp) and BL[p+7] != id(bp):
            evalu += p/8 - 4
    for p in bp.piecelist:
        if not(isSafe(p, BLACK)) and isSafe(p, WHITE):
            evalu += 0.4
        if p <= 39 and BL[p-8] == 0 and BL[p-9] != id(wp) and BL[p-7] != id(wp):
            evalu -= 5 - p/8

    if colour == BLACK:
        evalu *= -1

    if colour == WHITE:
        king, oppKing = wk.piecelist[0], bk.piecelist[0]
    else:
        king, oppKing = bk.piecelist[0], wk.piecelist[0]

    # Try to limit the enemy king's movement
    a = len(PieceMovement(oppKing))

    if a < 2:
        evalu += 3
    elif a < 3:
        evalu += 1.5
    elif a < 4:
        evalu += 1
    elif a < 5:
        evalu += 0.7
    elif a < 6:
        evalu += 0.5

    if hasOpposition(king, oppKing):
        evalu += 0.5

    return evalu
    

def toCoords(start,end,name=None,capture=None):
    if not(name): name = pieceatsqr(start).name
    if not(capture): capture = pieceatsqr(end)
    if name == 'K':
        if abs(start-end) == 2: return 'O-O'
    elif abs(start-end) == 3: return 'O-O-O'
    pre = ('' if name == 'p' else name)
    if capture and name == 'p': pre += numtocoord(start)[0]
    if capture: pre += 'x'
    return pre + numtocoord(end)


pOn = lambda s,p: pm.boardlist[s] == id(p)
def queensGambit():
    if pm.boardlist[27] == id(wp) and pm.boardlist[26] == id(wp):
        return pm.boardlist[35] == id(bp)
def sicilian():
    if pm.boardlist[28] == id(wp) and pm.boardlist[21] == id(wn):
        return pm.boardlist[51] == id(bp) and pm.boardlist[34] == id(bp)
def kingsPawn():
    if pm.boardlist[28] == id(wp) and pm.boardlist[21] == id(wn):
        return pm.boardlist[57] == id(bn) and pm.boardlist[36] == id(bp)

FirstMoves = [(lambda: True, {(0, 0.3): (11, 27), (0.3, 0.6): (12, 28), (0.6, 0.9): (10, 26), (0.9, 1): (14, 22)})]
SecondMoves = [(partial(pOn, 26, wp), {(0, 0.75): (50, 34), (0.75, 1): (52, 36)}),
               (partial(pOn, 27, wp), {(0, 0.25): (62, 45), (0.25, 1): (51, 35)}),
               (partial(pOn, 28, wp), {(0, 0.5): (50, 34), (0.5, 1): (52, 36)})]
ThirdMoves = [(queensGambit, {(0, 0.5): (35, 26), (0.5, 1): (52, 44)}),
              (sicilian, {(0, 1): (51, 43)}), (kingsPawn, {(0, 1): (57, 42)})]
# Tuple-keyed dictionary of lists of tuples of (function, tuple-keyed dictionary of tuples)
openingDict = {(WHITE, 0): FirstMoves, (BLACK, 1): SecondMoves, (BLACK, 2): ThirdMoves}

# Finds possible opening moves for black
def OpeningMoves(colour, movenum, randnum):
    if movenum >= 3 and colour == BLACK:
        if pm.boardlist[27] == id(wn) and PieceMovement(62).count(45):
            if pm.boardlist[34] != id(bp) and pm.boardlist[36] != id(bp):
                return 62, 45
        if pm.boardlist[27] == id(wp) and pm.boardlist[26] == id(wp):
            if PieceMovement(62).count(45): # Nf6
                return 62, 45
    if (colour, movenum) in openingDict:
        moves = openingDict[(colour, movenum)]
        for (boolKey, m) in moves:
            if boolKey(): # Calls the bool function in the moves list
                for x in m:
                    if x[0] < randnum and randnum < x[1]:
                        return m[x]
    global move_num
    move_num = movenum                        
    default = FindBest(colour)
    return default.movestart, default.moveend


# Profiling to see what slows the engine down
if __name__ == '__main__':
    MovePiece(12, 28)
    MovePiece(52, 36)
    MovePiece(3, 12)
    cProfile.run('FindBest("b")')
