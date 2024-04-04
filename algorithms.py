def func(i): #FUNCTION THAT DEFINES THE CONVEX FUNCTION F IN THE TREE CASES WE SPECIFIED IN THE PAPER
    return (2**(i+1))-1

def create_windows(S, W, F, k, func, a):
    for i in range(0, int(math.log2(k)) + 1):
        S.append((int(k - (k // (2 ** i)) + 1)))
    for i in range(1, int(math.log2(k)) + 1):
        n = []
        for h in range(S[i - 1], S[i]):
            n.append(h)
        W.append(n)
    W.append([S[-1]])
    for g in range(0, len(W)-1): # last window does not need a query
        gap = int(len(W[g])//(func(g+1)-func(g)))
        if (gap >= a):
            for m in W[g][::gap]:
                F.append(m)
        else:
            for m in range(S[g], S[-1]+1, a):
                F.append(m)
            break
    if k == 10:
        F = [1,6,9]
    return S, W, F

def Follower_23(requests, k, pred, a=1, alpha=1):
    # DEFINE THE 3 SETS S,W,F THAT WE USE IN THE ROBUST PHASE
    S = []
    W = []
    F = []
    # Filling the sets S,W,F
    if (a == 1):
        S,W,F = create_windows(S,W,F,k,func,a=a)
    pred_gap = 0
    skip = 0  # SKIP IS USED TO DEFINE THE LENGTH OF ROBUST PHASE
    cache = [None] * k
    prediction = [None] * k # Predictor also starts with an empty cache
    fitf = OPT(requests, k, pred)  # FITF IS THE OPTIMAL CACHE
    unmarked = []  # UNMARKED IS THE SET OF UNMARKED pages
    marked = []   # MARKED IS THE SET OF MARKED pages
    history = [tuple(cache), ]  # HISTORY IS THE CACHE OF THE FOLLOWER AT EACH TIME t
    old = [] #Pages requested in the previous phase
    clean = [] #pages requested in the current phase
    total_pred = 0  #total number of predictions used
    follow_cost = 0
    belady_cost = 0
    last_seen = dict() # for LRU evictions
    for t, (request, next) in enumerate(zip(requests, pred)):
        last_seen[request] = t
        f = list(fitf[t]).copy() #optimal cache at time t
        # ALGORITHM ITSELF
        if request in cache:  # IF THE REQUESTED PAGE IS IN THE CACHE, DO NOTHING
            index_to_evict = cache.index(request)
            cache[index_to_evict] = request
        elif None in cache:  # IF THE CACHE IS NOT FULL, LOAD THE REQUESTED PAGE
            index_to_evict = cache.index(None)
            cache[index_to_evict] = request
            prediction = list(pred[t + 1]).copy()
            # We do not really need to ask for this prediction, we in fact
            # know what they are without quering the predictor
            # (any algorithm just loads a page), therefore we do not count them.
            # We take these predictions only to make sure the variable
            # is defined.
                  if request not in cache:
            index_to_evict = None
            if skip == 0: # WE ENTER THIS IF WE ARE NOT IN THE ROBUST PHASE
                follow_cost += 1
                if request not in f:
                    belady_cost +=1
                #if request not in prediction and request not in f: #LINE 3 OF OUR ALGORITHM 2 : FOLLOWER ;  # WE EVICT A RANDOM PAGE WHICH IS NOT IN THE PREDICTOR CACHE
                if request not in prediction and (follow_cost <= alpha * belady_cost):
                    # make sure that we don't do more than one query of the predictor per a requests
                    # if pred_gap<=0 is checked in the parent "if", then "else" is skipped and we jump to Robust phase
                    # if pred_gap<= is only checked here, "else" specifies the alternative choice for page to evict if we cannot query the predictor
                    if pred_gap <= 0:
                        prediction = pred[t+1]
                        pred_gap=a
                        dd = differ(cache, prediction)
                        total_pred += 1
                        index_to_evict = cache.index(random.choice(dd))
                        assert(cache[index_to_evict] not in prediction)
                        cache[index_to_evict] = request
                    else:
                        # LRU rule:
                        #evict = min((last_seen[x] if x in last_seen else -1, x) for x in cache)[1]  # LRU rule
                        #index_to_evict = cache.index(evict)
                        # Random rule:
                        index_to_evict = random.choice(range(k))
                        cache[index_to_evict] = request
                elif request in prediction: #THIS IS SYNCHRONIZATION WITH PREDICTOR
                    dd = differ(cache, prediction)
                    index_to_evict = cache.index(random.choice(dd))
                    cache[index_to_evict] = request
                else:
                    # ME: return back here
                    follow_cost = 0
                    belady_cost = 0
                    skip = k
                    old = []
                    for req in requests[t-1::-1]:
                        if (req not in old) and (req != request):
                            old.append(req)
                        if len(old) >= k:
                            break
                    assert(len(old)==k)
                    unmarked = old.copy()
                    cache = old.copy()
                    assert(request not in cache)
                    marked = []
                    unmarked_for_reload = []
                    clean = []
                              if skip != 0: # WE ARE IN THE ROBUST PHASE
                assert(request not in cache)
                if request not in marked: # This is arrival
                    skip -= 1
                    arrival_no = k-skip
                    if request in unmarked:
                        unmarked.remove(request)
                    if request not in marked:
                        marked.append(request)
                    assert(len(marked) == arrival_no)
                    if request not in old:
                        clean.append(request)
                    assert(len(unmarked) == k - (arrival_no - len(clean)))
                    #if ((a==1) and ((arrival_no in F) or (request in clean))) or ((a > 1) and (pred_gap <= 0)): # query a new predition, also in clean arrivals
                    if ((a==1) and (arrival_no in F)) or ((a > 1) and (pred_gap <= 0)): # query a new predition, only in F, no clean arrival
                        pred_gap = a
                        total_pred += 1
                        prediction = list(pred[t + 1]).copy()
                    if arrival_no in S:
                        # make a list of unmarked pages which are supposed to be loaded back to
                        # the cache. They will be loaded once requested and replaced by a page
                        # not present in the fresh prediction as a lazy sync with predictor
                        unmarked_for_reload = []
                        for p in unmarked:
                            if (p in prediction) and (p not in cache):
                                unmarked_for_reload.append(p)
                    #if (request in old) and (request in prediction_old):
                    if request in unmarked_for_reload:
                        # Lazy sync with predictor
                        assert(request not in cache)
                        dd = differ(cache, prediction)
                        index_to_evict = cache.index(random.choice(dd))
                        cache[index_to_evict] = request
                    if request in clean: # Clean arrival
                        #if request in prediction: # we must have a fresh prediction here, so we follow it
                        # Looks like even old predictions which don't contain request might help:
                            assert(request not in cache)
                            dd = differ(cache, prediction)
                            index_to_evict = cache.index(random.choice(dd))
                            cache[index_to_evict] = request
                                      if request not in cache: # Random eviction
                    index_to_evict = None
                    unmarked_slots = []
                    for page in cache:
                        if page in unmarked:
                            unmarked_slots.append(cache.index(page))
                    if (len(unmarked_slots) == 0):
                        print(arrival_no, len(clean), len(unmarked), len(marked), skip)
                        print(request in marked, request in unmarked, request in clean)
                        for page in cache:
                            print(page in unmarked)
                        print(cache)
                    index_to_evict = random.choice(unmarked_slots)
                    assert(request not in cache)
                    cache[index_to_evict] = request
                if skip == 0: # sync with marking cache
                    assert(len(marked) == k)
                    assert(len(unmarked) == len(clean))
                    #cache = marked.copy()
        history.append(tuple(cache))
        pred_gap -= 1
    #print("a", a, "instance_len", t, "total_pred", total_pred)
    return history, total_pred

