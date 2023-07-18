import sys
import PieceMovement as pm
from PieceMovement import *
from functools import partial
import cProfile
import time
import numpy as np
import random
#from engines import a

ENGINE="my-sf"
if ENGINE=="sf":
    hist = []#qs/ks==unsure
    import engines.sunfish.sunfish as sf
    from engines.sunfish.sunfish import Position as pos
    import engines.sunfish.tools.uci
if ENGINE=="my-sf":
    MOVETIME=2
    hist = []#qs/ks==unsure
    import engines.mySunfish.sunfish as sf
    from engines.mySunfish.sunfish import Position as pos
    import engines.mySunfish.tools.uci
def fileAndRank(sqr):
    return sqr%8, 7 - sqr//8

def getFen():
    piece_arr=np.array(["OO"]*64,dtype="<U2")
    
    for piece in allpieces:
        for f in piece.piecelist:
            piece_arr[f]=str(piece)
    fen=""
    for rank in piece_arr.reshape((8,8)):
        empty=0
        for file in rank:
            if file == "OO":
                empty+=1
            else:
                if file[0]=="w":
                    file=file[1].upper()
                else:
                    file=file[1].lower()
                if empty==0:
                    fen+=file
                else:
                    fen+=str(empty)
                    fen+=file
                    empty=0
            if empty==8:
                fen+=(str(8))
        fen+="/"
    return fen
def boardhash():
    fen=""
    for piece in allpieces:
        fen+=str(piece.piecelist)+str(piece)
    return fen
def getSfI(colour):
    ind=0
    out=[]
    piece_arr=np.array(["OO"]*64,dtype="<U2")
    
    for piece in allpieces:
        for f in piece.piecelist:
            piece_arr[f]=str(piece)
    out.insert(ind,"         \n")
    out.insert(ind,"         \n")

    for rank in piece_arr.reshape((8,8)):
        r=" "
        
        for file in rank:
            if file == "OO":
                r+="."
            else:
                if file[0]=="w":
                    file=file[1].upper()
                else:
                    file=file[1].lower()
                r+=file
        r+="\n"
        out.insert(ind,r)
    out.insert(ind,"         \n")
    out.insert(ind,"         \n")
    n=""
    for l in out: n+=l
    if colour==BLACK:
        n=n[::-1].swapcase()
    return n
                    
# Global Constants:
Pval = 1
Nval = 3
Bval = 3
Rval = 5
Qval = 9
Kval = 100

mateThreshold = Kval - 2*Qval - 2*Pval
DEPTH=3  # Change these numbers to change difficulty
maxWidth = 2**(DEPTH+1)        #
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
    def __str__(self):
        return f"{self.movestart}, {self.moveend}"
    
evals={}
deepEvals={}
lookups=0
deeplookups =0
# Returns the "best" move for colour
def FindBest(colour, depth=DEPTH, width=maxWidth, first=True):
        
    if ENGINE=="sf":
        cs=updateCastlingRights()
        hist.append(pos(getSfI(colour), 0, cs[0], cs[1], numtocoord(curState.enPassant), 0))
        b=engines.sunfish.tools.uci.bestMove(sf,hist)
        best=fromcoords(b)
        p= Position()
        p.evaluation=0
        p.movestart=best[0]
        p.moveend=best[1]
        p.mateIn=0
        p.coords=toCoords(best[0],best[1],str(pieceatsqr(best[0])),bool(pieceatsqr(best[1]))) 
        print(p)
        print(b)
        print(best)
        MovePiece(best[0],best[1])
        cs=updateCastlingRights()
        hist.append(pos(getSfI(colour), 0, cs[0], cs[1], numtocoord(curState.enPassant), 0))
        UndoMove()
        return p
        
    if ENGINE=="my-sf":
        
        cs=updateCastlingRights()
        hist.append(pos(getSfI(colour), 0, cs[0], cs[1], numtocoord(curState.enPassant), 0))
        b=engines.mySunfish.tools.uci.bestMove(sf,hist,MOVETIME)
        best=fromcoords(b)
        p= Position()
        p.evaluation=0
        p.movestart=best[0]
        p.moveend=best[1]
        p.mateIn=0
        p.coords=toCoords(best[0],best[1],str(pieceatsqr(best[0])),bool(pieceatsqr(best[1]))) 
        print(p)
        print(b)
        print(best)
        MovePiece(best[0],best[1])
        cs=updateCastlingRights()
        hist.append(pos(getSfI(colour), 0, cs[0], cs[1], numtocoord(curState.enPassant), 0))
        UndoMove()
        boards={}
        for pr in hist:
            if pr.board in boards:
                boards[pr.board]+=1
            else:
                boards[pr.board]=1
        print(max(boards.values()))
        
        return p





    old="""
    global lookups,deeplookups
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
    
    #print(getSfI())
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
                    fen=boardhash()
                    
                    if fen in deepEvals:
                        cur.evaluation=deepEvals[fen][0]
                        deeplookups+=1
                    elif fen in evals:
                        cur.evaluation=evals[fen]
                        lookups+=1
                    else:
                        cur.evaluation = EvaluatePosition(colour)
                        evals[fen]=cur.evaluation
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
                fen=boardhash()
                if fen in deepEvals:
                    cur.evaluation=deepEvals[fen][0]
                    deeplookups+=1
                elif fen in evals:
                    cur.evaluation=evals[fen]
                    lookups+=1
                else:
                    cur.evaluation = EvaluatePosition(colour)
                    evals[fen]=cur.evaluation
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
        fen=boardhash()
        if fen not in deepEvals or deepEvals[fen][2]<depth:
            
            oppTop = FindBest(opp, depth-1,int(width/2), False)

            if oppTop == 'C':
                pos.mateIn = 1
                pos.evaluation = Kval
            elif oppTop == 'S':
                pos.evaluation = 0
            else:
                if oppTop.mateIn: pos.mateIn = oppTop.mateIn + 1

                pos.evaluation = (-1) * oppTop.evaluation
                deepEvals[fen]=(pos.evaluation,oppTop,depth+1)
        else:
            deeplookups+=1
            pos.evaluation,oppTop,_=deepEvals[fen]
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
    #random.shuffle(topMoves)
    best = max(topMoves, key=e)

    if first:
        if NOISY_LOGGING:
            print ("Time:", current_time_millis() - time0)
            print(f"dictSize: {evals.__len__()+deepEvals.__len__()}")
            print(f"lookups: {lookups}")
            print(f"deeplookups: {deeplookups}")
            print(best)
            hist = [sf.Position(getSfI(colour), 0, (True, True), (True, True), 0, 0)]
            import engines.sunfish.tools.uci
            print(fromcoords(engines.sunfish.tools.uci.bestMove(sf,hist[-1])))
            print(type(best))
            print(getSfI(colour))
            print(getSfI(colour).__len__())
            print ("---------")

        if best.evaluation <= -(mateThreshold) and width <= maxWidth:
            return FindBest(colour, depth+1, maxWidth*2, False)

    return best"""


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
def fromcoords(cs):
    cF={"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}

    return (cF[cs[0]]+(int(cs[1])-1)*8,cF[cs[2]]+(int(cs[3])-1)*8)


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
#def OpeningMoves(colour, movenum, randnum):
#    if movenum >= 3 and colour == BLACK:
#        if pm.boardlist[27] == id(wn) and PieceMovement(62).count(45):
#            if pm.boardlist[34] != id(bp) and pm.boardlist[36] != id(bp):
#                return 62, 45
#        if pm.boardlist[27] == id(wp) and pm.boardlist[26] == id(wp):
#            if PieceMovement(62).count(45): # Nf6
#                return 62, 45
#    if (colour, movenum) in openingDict:
#        moves = openingDict[(colour, movenum)]
#        for (boolKey, m) in moves:
#            if boolKey(): # Calls the bool function in the moves list
#                for x in m:
#                    if x[0] < randnum and randnum < x[1]:
#                        return m[x]
#    global move_num
#    move_num = movenum                        
#    default = FindBest(colour)
#    return default.movestart, default.moveend


    
# Profiling to see what slows the engine down
if __name__ == '__main__':
    print(getSfI(WHITE))
    MovePiece(12, 28)
    print(getSfI(BLACK))
    MovePiece(52, 36)
    print(getSfI(WHITE))
    MovePiece(3, 12)
    print(getSfI(BLACK))
    print("--ignore")
    print(getSfI(WHITE))
    cProfile.run('FindBest("b")')
    
    