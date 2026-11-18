import json, os, sys, urllib.request, urllib.error
from random import Random

ENV = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")
BUDGET = int(os.environ.get("NODES", "60000"))
MATE = 100000
INF = 1000000

VAL = (0, 100, 320, 330, 500, 900, 0)
# Piece-square tables, rank 1 first, index = rank*8+file. From white's view.
PST = (None,
(0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5, 0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10, 50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0),
(-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,5,5,0,-20,-40, -30,5,10,15,15,10,5,-30, -30,0,15,20,20,15,0,-30, -30,5,15,20,20,15,5,-30, -30,0,10,15,15,10,0,-30, -40,-20,0,0,0,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50),
(-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10, -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10, -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10, -10,0,0,0,0,0,0,-10, -20,-10,-10,-10,-10,-10,-10,-20),
(0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 5,10,10,10,10,10,10,5, 0,0,0,0,0,0,0,0),
(-20,-10,-10,-5,-5,-10,-10,-20, -10,0,5,0,0,0,0,-10, -10,5,5,5,5,5,0,-10, 0,0,5,5,5,5,0,-5, -5,0,5,5,5,5,0,-5, -10,0,5,5,5,5,0,-10, -10,0,0,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20),
(20,30,10,0,0,10,30,20, 20,20,0,0,0,0,20,20, -10,-20,-20,-20,-20,-20,-20,-10, -20,-30,-30,-40,-40,-30,-30,-20, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30))
KE = (-50,-30,-30,-30,-30,-30,-30,-50, -30,-30,0,0,0,0,-30,-30, -30,-10,20,30,30,20,-10,-30, -30,-10,30,40,40,30,-10,-30, -30,-10,30,40,40,30,-10,-30, -30,-10,20,30,30,20,-10,-30, -30,-20,-10,0,0,-10,-20,-30, -50,-40,-30,-20,-20,-30,-40,-50)

KN = (33, 31, 18, 14, -33, -31, -18, -14)
KG = (1, -1, 16, -16, 15, 17, -15, -17)
BD = (15, 17, -15, -17)
RD = (1, -1, 16, -16)
CMASK = [15] * 128
for _sq, _m in ((4, 12), (7, 14), (0, 13), (116, 3), (119, 11), (112, 7)):
    CMASK[_sq] = _m

B = [0] * 128
S = 1
C = 0
E = -1
H = 0
KW = 4
KB = 116
TT = {}
ND = [0]
PATH = set()
KILL = [[0, 0] for _ in range(128)]


def on(s):
    return 0 <= s < 128 and not (s & 0x88)


def atk(sq, by):
    if by > 0:
        for s in (sq - 15, sq - 17):
            if on(s) and B[s] == 1:
                return True
    else:
        for s in (sq + 15, sq + 17):
            if on(s) and B[s] == -1:
                return True
    for d in KN:
        s = sq + d
        if on(s) and B[s] == 2 * by:
            return True
    for d in KG:
        s = sq + d
        if on(s) and B[s] == 6 * by:
            return True
    for d in BD:
        s = sq + d
        while on(s):
            p = B[s]
            if p:
                if p == 3 * by or p == 5 * by:
                    return True
                break
            s += d
    for d in RD:
        s = sq + d
        while on(s):
            p = B[s]
            if p:
                if p == 4 * by or p == 5 * by:
                    return True
                break
            s += d
    return False


def gen(caps_only=False):
    ms = []
    for sq in range(128):
        if sq & 0x88:
            continue
        p = B[sq]
        if p * S <= 0:
            continue
        t = abs(p)
        if t == 1:
            d = 16 * S
            fwd = sq + d
            if on(fwd) and B[fwd] == 0:
                last = (fwd >> 4) == (7 if S > 0 else 0)
                if last:
                    for pr in (5, 4, 3, 2):
                        ms.append(sq | fwd << 7 | pr << 14)
                elif not caps_only:
                    ms.append(sq | fwd << 7)
                    if (sq >> 4) == (1 if S > 0 else 6):
                        fwd2 = sq + 2 * d
                        if B[fwd2] == 0:
                            ms.append(sq | fwd2 << 7)
            for df in (-1, 1):
                cap = sq + d + df
                if not on(cap):
                    continue
                if B[cap] * S < 0:
                    last = (cap >> 4) == (7 if S > 0 else 0)
                    if last:
                        for pr in (5, 4, 3, 2):
                            ms.append(sq | cap << 7 | pr << 14)
                    else:
                        ms.append(sq | cap << 7)
                elif cap == E:
                    ms.append(sq | cap << 7)
        elif t == 2 or t == 6:
            for d in (KN if t == 2 else KG):
                to = sq + d
                if on(to) and B[to] * S <= 0 and (not caps_only or B[to]):
                    ms.append(sq | to << 7)
        else:
            for d in (BD if t == 3 else RD if t == 4 else BD + RD):
                to = sq + d
                while on(to):
                    if B[to] == 0:
                        if not caps_only:
                            ms.append(sq | to << 7)
                    else:
                        if B[to] * S < 0:
                            ms.append(sq | to << 7)
                        break
                    to += d
    if not caps_only:
        if S > 0:
            if C & 1 and B[5] == 0 and B[6] == 0 and B[7] == 4 and B[4] == 6 and not atk(4, -1) and not atk(5, -1) and not atk(6, -1):
                ms.append(4 | 6 << 7)
            if C & 2 and B[3] == 0 and B[2] == 0 and B[1] == 0 and B[0] == 4 and B[4] == 6 and not atk(4, -1) and not atk(3, -1) and not atk(2, -1):
                ms.append(4 | 2 << 7)
        else:
            if C & 4 and B[117] == 0 and B[118] == 0 and B[119] == -4 and B[116] == -6 and not atk(116, 1) and not atk(117, 1) and not atk(118, 1):
                ms.append(116 | 118 << 7)
            if C & 8 and B[115] == 0 and B[114] == 0 and B[113] == 0 and B[112] == -4 and B[116] == -6 and not atk(116, 1) and not atk(115, 1) and not atk(114, 1):
                ms.append(116 | 114 << 7)
    return ms


STK = []


def make(m):
    global C, E, H, S, KW, KB
    frm = m & 127
    to = (m >> 7) & 127
    pr = (m >> 14) & 7
    p = B[frm]
    cap = B[to]
    cap_sq = to
    if abs(p) == 1 and to == E and cap == 0:
        cap_sq = to - 16 * S
        cap = B[cap_sq]
        B[cap_sq] = 0
    STK.append((m, cap, cap_sq, C, E, H))
    B[frm] = 0
    B[to] = pr * S if pr else p
    if abs(p) == 6:
        if S > 0:
            KW = to
        else:
            KB = to
        if abs(to - frm) == 2:
            if to > frm:
                rf, rt = to + 1, to - 1
            else:
                rf, rt = to - 2, to + 1
            B[rt] = B[rf]
            B[rf] = 0
    C &= CMASK[frm] & CMASK[to]
    E = frm + 16 * S if abs(p) == 1 and abs(to - frm) == 32 else -1
    H = 0 if abs(p) == 1 or cap else H + 1
    S = -S


def unmake():
    global C, E, H, S, KW, KB
    m, cap, cap_sq, c, e, h = STK.pop()
    frm = m & 127
    to = (m >> 7) & 127
    pr = (m >> 14) & 7
    p = B[to]
    S = -S
    if abs(p) == 6:
        if S > 0:
            KW = frm
        else:
            KB = frm
        if abs(to - frm) == 2:
            if to > frm:
                rf, rt = to + 1, to - 1
            else:
                rf, rt = to - 2, to + 1
            B[rf] = B[rt]
            B[rt] = 0
    B[frm] = S if pr else p
    B[to] = 0
    B[cap_sq] = cap
    C, E, H = c, e, h


def parse_fen(fen):
    global B, S, C, E, H, KW, KB
    parts = fen.split()
    B = [0] * 128
    r = 7
    f = 0
    for ch in parts[0]:
        if ch == '/':
            r -= 1
            f = 0
        elif ch.isdigit():
            f += int(ch)
        else:
            v = "PNBRQK".index(ch.upper()) + 1
            B[r * 16 + f] = v if ch.isupper() else -v
            f += 1
    S = 1 if parts[1] == 'w' else -1
    C = 0
    if parts[2] != '-':
        for ch in parts[2]:
            C |= {'K': 1, 'Q': 2, 'k': 4, 'q': 8}[ch]
    E = -1 if parts[3] == '-' else (int(parts[3][1]) - 1) * 16 + (ord(parts[3][0]) - 97)
    H = int(parts[4]) if len(parts) > 4 else 0
    for sq in range(128):
        if B[sq] == 6:
            KW = sq
        elif B[sq] == -6:
            KB = sq


def key():
    return (tuple(B), S, C, E)


def evaluate():
    s = 0
    bish = [0, 0]
    end = True
    for sq in range(128):
        if sq & 0x88:
            continue
        p = B[sq]
        if not p:
            continue
        t = abs(p)
        if t == 5:
            end = False
        if t == 3:
            bish[0 if p > 0 else 1] += 1
        i = (sq >> 4) * 8 + (sq & 7)
        if t == 6:
            tab = KE if end else PST[6]
            v = tab[i if p > 0 else i ^ 56]
        else:
            v = VAL[t] + PST[t][i if p > 0 else i ^ 56]
        s += v if p > 0 else -v
    if bish[0] == 2:
        s += 30
    if bish[1] == 2:
        s -= 30
    return s * S


class Stop(Exception):
    pass


def order(moves, tt_move, ply):
    def score(m):
        if m == tt_move:
            return 1000000
        to = (m >> 7) & 127
        cap = B[to]
        if cap:
            return 10000 + 10 * VAL[abs(cap)] - VAL[abs(B[m & 127])] // 10
        if m == KILL[ply][0]:
            return 9000
        if m == KILL[ply][1]:
            return 8000
        return 0
    moves.sort(key=score, reverse=True)
    return moves


def qs(alpha, beta, ply):
    ND[0] += 1
    if ND[0] > BUDGET:
        raise Stop
    k = key()
    if k in PATH:
        return 0
    ent = TT.get(k)
    if ent:
        sc, fl = ent[1], ent[2]
        if fl == 0:
            return sc
        if fl == 1 and sc >= beta:
            return sc
        if fl == 2 and sc <= alpha:
            return sc
    stand = evaluate()
    if stand >= beta:
        TT[k] = (0, beta, 1, 0)
        return beta
    if stand > alpha:
        alpha = stand
    caps = []
    for m in gen(True):
        to = (m >> 7) & 127
        cap = B[to]
        pr = (m >> 14) & 7
        gain = (VAL[abs(cap)] if cap else 100) + (800 if pr else 0)
        caps.append(((-gain, VAL[abs(B[m & 127])]), m))
    caps.sort()
    best = alpha
    for (neg_gain, _), m in caps:
        if stand - neg_gain + 200 < alpha:
            break  # delta pruning: no later capture can reach alpha
        make(m)
        if atk(KW if S < 0 else KB, S):
            unmake()
            continue
        sc = -qs(-beta, -alpha, ply + 1)
        unmake()
        if sc >= beta:
            TT[k] = (0, beta, 1, m)
            return beta
        if sc > best:
            best = sc
            if sc > alpha:
                alpha = sc
    if best > stand:
        TT[k] = (0, best, 0, 0)
    return best


def search(depth, alpha, beta, ply):
    global S, E
    ND[0] += 1
    if ND[0] > BUDGET:
        raise Stop
    k = key()
    if k in PATH:
        return 0
    ent = TT.get(k)
    tt_move = 0
    if ent and ent[0] >= depth:
        sc, fl, bm = ent[1], ent[2], ent[3]
        tt_move = bm
        if fl == 0:
            return sc
        if fl == 1 and sc >= beta:
            return sc
        if fl == 2 and sc <= alpha:
            return sc
    if depth <= 0:
        return qs(alpha, beta, ply)
    in_chk = atk(KW if S > 0 else KB, -S)
    if depth >= 3 and ply > 0 and not in_chk:
        # null move
        e0 = E
        E = -1
        S = -S
        PATH.add(k)
        try:
            sc = -search(depth - 3, -beta, -beta + 1, ply + 1)
        finally:
            S = -S
            E = e0
            PATH.discard(k)
        if sc >= beta:
            return beta
    PATH.add(k)
    moves = order(gen(), tt_move, ply)
    best = -INF
    bestm = 0
    legal = 0
    a = alpha
    try:
        for m in moves:
            make(m)
            if atk(KW if S < 0 else KB, S):
                unmake()
                continue
            legal += 1
            sc = -search(depth - 1, -beta, -a, ply + 1)
            unmake()
            if sc > best:
                best = sc
                bestm = m
            if sc > a:
                a = sc
                if a >= beta:
                    if B[(m >> 7) & 127] == 0:
                        if KILL[ply][0] != m:
                            KILL[ply][1] = KILL[ply][0]
                            KILL[ply][0] = m
                    break
    finally:
        PATH.discard(k)
    if legal == 0:
        return -MATE + ply if in_chk else 0
    fl = 0 if best <= alpha else (1 if best >= beta else 0)
    if best <= alpha:
        fl = 2
    elif best >= beta:
        fl = 1
    else:
        fl = 0
    TT[k] = (depth, best, fl, bestm)
    return best


def uci_to_move(u):
    frm = (int(u[1]) - 1) * 16 + (ord(u[0]) - 97)
    to = (int(u[3]) - 1) * 16 + (ord(u[2]) - 97)
    pr = 0
    if len(u) == 5:
        pr = "nbrq".index(u[4]) + 2
    return frm | to << 7 | pr << 14


def move_to_uci(m):
    frm = m & 127
    to = (m >> 7) & 127
    s = "abcdefgh"[frm & 7] + str((frm >> 4) + 1) + "abcdefgh"[to & 7] + str((to >> 4) + 1)
    pr = (m >> 14) & 7
    if pr:
        s += "nbrq"[pr - 2]
    return s


def choose(legal):
    if len(legal) == 1:
        return legal[0]
    moves = [uci_to_move(u) for u in legal]
    ND[0] = 0
    best = legal[0]
    try:
        for depth in range(1, 64):
            a = -INF
            cur = None
            cur_sc = -INF
            for m in moves:
                make(m)
                sc = -search(depth - 1, -INF, -a, 1)
                unmake()
                if sc > cur_sc:
                    cur_sc = sc
                    cur = m
                if sc > a:
                    a = sc
            if cur is not None:
                best = move_to_uci(cur)
    except Stop:
        pass
    return best


def post(path, body):
    req = urllib.request.Request(ENV + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def main():
    global PATH
    while True:
        g = post("/game", {})
        if g["status"] == "done":
            break
        while g["status"] == "your_move":
            parse_fen(g["fen"])
            # collect history position keys for repetition awareness
            hist = set()
            try:
                saved = (B[:], S, C, E, H, KW, KB)
                parse_fen(g["start_fen"])
                hist.add(key())
                for u in g.get("moves", []):
                    make(uci_to_move(u))
                    hist.add(key())
                B[:], S, C, E, H, KW, KB = saved[0], saved[1], saved[2], saved[3], saved[4], saved[5], saved[6]
            except Exception:
                hist = set()
            PATH = set(hist)
            mv = choose(g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": mv})
        print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
    print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)


if __name__ == "__main__":
    main()
