# Copyright (c) 2005-2006 Nanorex, Inc.  All rights reserved.
'''
state_utils.py

General state-related utilities.

$Id$
'''
__all__ = ['copy_val'] # __all__ must be the first symbol defined in the module.

    #e was the old name (copy_obj) better than copy_val??

__author__ = 'bruce'

# == public definitions

class _eq_id_mixin_: ##e use more (GLPane?); renamed from _getattr_efficient_eq_id_mixin_
    """For efficiency, any objects defining __getattr__ which might frequently be compared
    with == or != or coerced to a boolean, should have definitions for __eq__ and __ne__ and __nonzero__
    (and any others we forgot??), even if those are semantically equivalent to Python's behavior when they don't.
    Otherwise Python has to call __getattr__ on each comparison of these objects, just to check whether
    they have one of those special method definitions (potentially as a value returned by __getattr__).
       This mixin class provides definitions for those methods. It's ok for a class to override some of these.
    It can override both __eq__ and __ne__, or __eq__ alone, but should not normally override __ne__ alone,
    since our definition of __ne__ is defined as inverse of object's __eq__.
       These definitions are suitable for objects meant as containers for "named" mutable state
    (for which different objects are never equal, even if their *current* state is equal, since their future
    state might not be). They are not suitable for data-like objects. This is why the name contains _eq_id_
    rather than _eq_data_. For datalike objects, there is no shortcut to defining each of these methods in
    a customized way (and that should definitely be done, for efficiency, under same conditions in which use
    of this mixin is recommended). We might still decide to make an _eq_data_mixin_(?) class for them, for some other reason.
    """
    #bruce 060209
    def __eq__(self, other):
        return self is other
    def __ne__(self, other):
        ## return not (self == other) # presumably this uses self.__eq__ -- would direct use be faster?
        return not self.__eq__(other)
    def __nonzero__(self): ###k I did not verify in Python docs that __nonzero__ is the correct name for this! [bruce 060209]
        ## return self is not None # of course it isn't!
        return True
    def __hash__(self): #####k guess at name; guess at need for this due to __eq__, but it did make our objects ok as dict keys again
        return id(self) #####k guess at legal value
    pass

def copy_val(obj):
    """Copy obj, leaving no shared mutable components between copy and original,
    assuming (and verifying) that obj is a type we consider (in nE-1) to be a
    "standard data-like type", and using our standard copy semantics for such types.
    (These standards are not presently documented except in the code of this module.)
       #e In the future, additional args will define our actions on non-data-like Python objects
    (e.g. Atom, Bond, Node), for example by providing an encoding filter for use on them which might
    raise an exception if they were illegal to pass, and we might even merge the behaviors of this function
    and the ops_copy.Copier class; for now, all unrecognized types or classes are errors
    if encountered in our recursive scan of obj (at any depth).
       We don't handle or check for self-reference in obj -- that would always be an error;
    it would always cause infinite recursion in the present implem of this function.
       We don't optimize for shared subobjects within obj. Each reference to one of those
    is copied separately, whether it's mutable or immutable. This could be easily fixed if desired.
    """
    return copy_run().copy_val(obj) # let's hope the helper gets deleted automatically if it saves any state (it doesn't now)

# == helper code

from Numeric import array, PyObject

numeric_array_type = type(array(range(2)))

class copy_run: # might have called it Copier, but that conflicts with the ops_copy.py class; rename it again if it becomes public
    "one instance exists to handle one copy-operation of some python value, of the kind we use in copyable attributes"
    #e the reason it's an object is so it can store options given to the function copy_val, when we define those.
    #e such options would affect what this does for python objects it doesn't always copy.
    atomic_types = tuple( map(type, (1, 1.0, "x", u"x", None, True)) ) #e also complex (a python builtin type)?
    def __init__(self):
        ##e might need args for how to map pyobjs, or use subclass for that...
        #e ideal might be a func to copy them, which takes our own copy_val method...
        pass ## not needed: self.memo = {} # maps id(obj) to obj for objs that might contain self-refs
    def copy_val(self, obj):
        t = type(obj)
        if t in self.atomic_types:
            return obj
        #e memo check? not yet needed. if it is, see copy module (python library) source code for some subtleties.
        copy = self.copy_val
        if t is type([]):
            return map( copy, obj )
        if t is type(()):
            #e note: we don't yet bother to optimize by avoiding the copy when the components are immutable,
            # like copy.deepcopy does.
            return tuple( map( copy, obj ) )
        if t is type({}):
            res = {}
            for key, val in obj.iteritems():
                key = copy(key) # might not be needed or even desirable; ok for now
                val = copy(val)
                res[key] = val #e want to detect overlaps as errors? to be efficient, could just compare lengths.
            assert len(res) == len(obj) # for now
            return res
        #e Numeric array
        if t is numeric_array_type:
            if obj.typecode() == PyObject:
                return array( map( copy, obj) )
                # we don't know whether the copy typecode should be PyObject (eg if they get encoded),
                # so let it be inferred for now... fix this when we see how this needs to be used,
                # by requiring it to be declared, since it relates to the mapping of objects...
                # or by some other means.
            return obj.copy() # use Numeric's copy method for Character and number arrays ###@@@ verify ok from doc of this method...
        # Handle data-like objects which declare themselves as such.
        # Note: we have to use our own method name and API, since its API can't be made compatible
        # with the __deepcopy__ method used by the copy module (since that doesn't call back to our own
        # supplied copy function for copying parts, only to copy.deepcopy).
        #e We might need to revise the method name, if we split the issues of how vs whether to deepcopy an object.
        try:
            method = obj._s_deepcopy
            # This should be defined in any object which should *always* be treated as fully copied data.
            # Presently this includes VQT.Q (quats), and maybe class gamessParms.
        except AttributeError:
            pass
        else:
            return method( self.copy_val) # (passing copy_val wouldn't be needed if we knew obj only contained primitive types)
        # Special case for QColor; if this set gets extended we can use some sort of table and registration mechanism.
        # We do it by name so this code doesn't need to import QColor.
        if obj.__class__.__name__ == 'qt.QColor':
            return _copy_QColor(obj) # extra arg for copyfunc is not needed
        #e future: if we let clients customize handling of classes like Atom, Bond, Node,
        # they might want to encode them, wrap them, copy them, or leave them as unchanged refs.
        #
        # Unknown or unexpected pyobjs will always be errors
        # (whether or not they define copy methods of some other kind),
        # though we might decide to make them print a warning rather than assertfailing,
        # once this system has been working for long enough to catch the main bugs.
        assert 0, "uncopyable by copy_val: %r" % (obj,)
    pass

def _copy_QColor(obj):
    from qt import QColor
    assert obj.__class__ is QColor
    return QColor(obj)

# ==

class scanner: #bruce 060209, a work in progress (not yet called or correct)
    def __init__(self, start_objs):
        self.todo = start_objs #e put in list, so ok if contains dups?
        self.seen_objs = {} # maps id(obj) to obj, for objs seen before... ### don't we need to store them more permanently?
        ## or do we reuse this scanner object multiple times? and, seen before is one thing, seen in this scan is another...
        self.encoded_objs = {} # maps id(obj) to encoded_obj, only for objs that should be encoded when present in value-diffs
    def explore_all(self, starting_todo):
        # objs in self.todo are the ones we still need to scan - each is being seen for the first time (already checked if seen before)
        ##e we'll have several levels of todo ((structure, selection, view) x (provisional)), scan them in order...
        todo = list(starting_todo)
        ###e maybe scan it as vals instead? or as one val... but no diffs?? hmm? what do ppl want as roots - most flex is vals.
        while self.todo:
            self.newtodo = [] # used in explore
            todo = self.todo
            self.todo = 333
            for obj in todo:
                self.explore(obj) # explore obj for more objs, store diffs/vals found in obj somewhere, append unseen objs to newtodo
                encoded = self.new_encoding(obj) ###e WRONG, no, don't redo if seen in prior scan (I think)
                if encoded is not obj:
                    self.encoded_objs[id(obj)] = encoded
                # self.seen_objs[id(obj)] = obj # just this scan... actually didn't this happen earlier when we first encountered obj? YES
                continue #??
            self.todo = self.newtodo
        return
    def explore(self, obj):
        ###e seen it ever? seen it this scan? needs encoding? (figure that out first, in case it refs itself in some attr)
        # if it's new: store that stuff, then:
        # figure out its type, and thus its attr-policy-map (or ask it)
        objid # for this, take time to find a nice key (small int); might just have a map from id(obj) to that
        for attr, val in obj.__dict__.iteritems():
            # figure policy of this attr, and dict to store valdiffs in if we're doing that, also whether it's structure or sel etc
            this_attrs_diffs
            # and of course whether to proceed
            oldval = this_attrs_last_seen_state[objid] ##e encoded??? (always copied) # we have this for *every* attrval... so store it below!
            #e if we don't have an oldval...
            if val != oldval:
                # val differs, needs two things:
                # - exploring for new objs
                # - storing as a diff
                ##### what about scanning objs that are not found as diffs, but might have diffs inside them?
                # do we depend on change tracking to report them to us? or, rescan some or all attrs every time? ###e
                encoded = self.explore_copy_encode_val(val) # stores new stuff on newtodo, i guess... hmm, same method should also copy/encode val
                ###e check again for != in case encoding made it equal??? (rethink when we need some encoding someday? we don't yet)
                this_attrs_diffs[objid] = oldval
                this_attrs_last_seen_state[objid] = encoded # not val? also val? hmm... consider need seply for copy, encode, in val ####e
            continue
        return
    pass
    
# == test code

def _test():
    print "testing some simple cases of copy_val"
    map( _test1, [2,
                  3,
                  "string",
                  [4,5],
                  (6.0,),
                  {7:8,9:10},
                  array([2,3]),
                  None] )
    print "done"

def _test1(obj): #e perhaps only works for non-pyobj types for now
    if obj != copy_val(obj):
        print "failed for %r" % (obj,)

if __name__ == '__main__':
    _test()

# end
