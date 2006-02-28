# Copyright (c) 2005-2006 Nanorex, Inc.  All rights reserved.
'''
state_utils.py

General state-related utilities.

$Id$
'''
__author__ = 'bruce'

from state_constants import *
import types
import env

### TODO:
'''
Where is _s_deepcopy (etc) documented? (In code and on wiki?)

That should say:

- When defining _s_deepcopy, consider:

  - is it correct for any copyfunc argument? (esp in its assumption about what that returns, original or copy or transformed copy)
  
  - is its own return value __eq__ to the original? It should be, so you have to define __eq__ AND __ne__ accordingly.
  
  - should you define _s_scan_children to, to scan the same things copied? (Only if they are instance objects, and are "children".
    See S_CHILDREN doc for what that means.)

Did the above for VQT and jigs_planes, still no __eq__ or children for jig_Gamess -- I'll let that be a known bug I fix later,
to test the behavior of my error detect/response code.
Also, when I do fix it (requires analyzing jig_Gamess contents) I might as well turn it into using a mixin
to give it a proper __eq__ based on declaring the state attrs! 
####@@@@

I might as well put state decls into the archived-state objects I'm creating, so they too could be compared by __eq__ and diffed!!!
(Actually, that won't work for diff since it has to descend into their dictionaries in an intelligent way.
 But it might work for __eq__.)

This means my archived-state objects should really be objects, not just tuples or dicts.
Let's change the code that collects one to make this true. Search for... attrdict?

S_CHILDREN: we might need a decl that we have no children (so don't warn me about that), and a reg for external classes of the same.

And certainly we need to go through the existing stateholder classes (e.g. Node) and add their attr/child decls.
Maybe rather than accomodating copyable_attrs, we'll just replace it? Not sure, maybe later (a lot of things use it).

Do any inapprop obs get a key (like data or foreign objs) in current code?? #####@@@@@
'''

# ==

class _UNSET_class:
    "[private class for _UNSET_, which sometimes represents unset attribute values; there should be only one instance]"
    #e can we add a decl that makes the _s_attr system notice the bug if it ever hits this value in a real attrval? (should we?)
    def __repr__(self):
        return "_UNSET_"
    pass

try:
    _UNSET_ # ensure only one instance, even if we reload this module
except:
    _UNSET_ = _UNSET_class() ####@@@@ need to use this in the _s_attr / Undo code


# ==

class _eq_id_mixin_: ##e use more? (GLPane?)
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

# ==

def transclose( toscan, collector ):
    """General transitive closure routine using dictionaries for collections in its API,
    where the keys can be whatever you want as long as they are unique (for desired equiv classes of objects)
    and used consistently.
       Details: Toscan should be a dictionary whose values are the starting point for the closure,
    and collector(obj1, dict1) should take one such value obj1 (never passed to it before)
    and for each obj it finds from obj1 (in whatever way it wants -- that defines the relation we're transitively closing),
    store it as a new value in dict1 (with appropriate consistent key).
       We don't modify toscan, and we return a new dictionary (with consistent keys) whose values
    are all the objects we found. Collector will have been called exactly once on each object we return.
    It must not modify toscan (since we use itervalues on it while calling collector),
    at least when it was called on one of the values in toscan.
    """
    # We have three dicts at a time: objects we're finding (not being checked for newness yet),
    # objects we're scanning to look for those, and objects seen (i.e. done with or being scanned).
    # Keys are consistent in all these dicts (and should be as unique as objects need to be distinct),
    # but what they actually are is entirely up to our args (but they must be consistent between the two args as well).
    # [#doc: need to explain that better]
    seen = dict(toscan)
    while toscan:
        found = {}
        for obj in toscan.itervalues():
            collector(obj, found) #e might the collector also want to know the key??
        # now "subtract seen from found"
        new = {}
        for key, obj in found.iteritems():
            if not seen.has_key(key):
                new[key] = obj
        seen.update(new)
        toscan = new
        continue
    return seen

# ==

class Classification: #e want _eq_id_mixin_? probably not, since no getattr.
    """Classifications record policies and methods for inspecting/diffing/copying/etc all objects of one kind,
    or can be used as dict keys for storing those policies externally.
    (By "one kind of object", we often mean the instances of one Python class, but not always.)
    """
    pass

# possible future optim: some of these could be just attrholders, not instances, so their methods wouldn't require 'self'...
# OTOH some of them do make use of self, and, we might put generic methods on the superclass.
# ... ok, leave it like this for now, and plan to turn it into C code someday; or, use class methods.
# (or just use these subclasses but define funcs outside and store them as attrs on the sole instances)

###@@@ not yet clear if these simple ones end up being used...

class AtomicClassification(Classification):
    """Atomic (immutable, part-free) types can be scanned and copied trivially....
    """
##    def scan(self, val, func):
##        "call func on nontrivial parts of val (what this means precisely is not yet defined)"
##        pass
    def copy(self, val, func):
        "copy val, using func to copy its parts"
        return val
    pass

class ListClassification(Classification):
    "Classification for Lists (or maybe any similar kind of mutable sequences?)"
##    def scan(self, val, func):
##        "call func on all parts of val"
##        for part in val:
##            func(part)
    def copy(self, val, func):
        "copy val, using func for nontrivial parts"
        return map( func, val) #e optimize by changing API to be same as map, then just using an attrholder, holding map?
    pass

def copy_list(val):
    return map(copy_val, val)

def scan_list(val, func):
    for elt in val:
        func(elt)
    return

class DictClassification(Classification):
    def copy(self, val, func):
        res = {} #e or use same type or class as val? not for now.
        for key, val1 in val.iteritems():
            # as an optim, strictly follow a convention that dict keys are immutable so don't need copying
            res[key] = func(val1)
        return res
    pass

def copy_dict(val):
    res = {}
    for key, val1 in val.iteritems():
        res[key] = copy_val(val1)
    return res

def scan_dict(dict1, func):
    for elt in dict1.itervalues(): # func must not harm dict1
        func(elt)
    return

class TupleClassification(Classification):
    def copy(self, val, func):
        """simple version should be best for now
        """
        return tuple(map(func, val))
            # not worth the runtime to save memory by not copying if all parts immutable; save that for the C version.
    pass

def copy_tuple(val):
    return tuple(map(copy_val, val))

scan_tuple = scan_list

# Tuple of state attr decl values used for attrs which hold "defining state",
# which means state that should (usually) be saved, compared, copied, tracked/changed by Undo, etc.
# Should not include attrs recomputable from these, even if as an optim we sometimes track or save them too (I think).

STATE_ATTR_DECLS = (S_DATA, S_CHILD, S_CHILDREN, S_REF, S_REFS, S_PARENT, S_PARENTS) # but not S_CACHE, S_JUNK(?), etc
    #e refile in state_constants.py ? not sure, since it's not needed outside this module

class InstanceClassification(Classification): #k used to be called StateHolderInstanceClassification; not yet sure of scope
    # we might decide to have a helper func classify an instance and return one of several classes, or None-or-so...
    # i mean some more atomic-like classification for classes that deserve one... [060221 late]
    #k not sure if this gains anything from its superclass
    """###doc, implem - hmm, why do we use same obj for outside and inside? because, from outside, you might add to explore-list...
    """
    def __init__(self, class1):
        "Become a Classification for class class1 (applicable to its instances)"
        self.policies = {} # maps attrname to policy for that attr #k format TBD, now a map from attrname to decl val
        self.class1 = class1
        self.attrs_with_no_dflt = [] # public list of attrs with no declared or evident default value (might be turned into a tuple)
        self.attr_dflt_pairs = [] # public list of attr, dflt pairs, for attrs with a default value (has actual value, not a copy)
        self.dict_of_all_state_attrs = {}
        self.categories = {} # (public) categories (e.g. 'selection', 'view') for attrs which declare them using _s_categorize_xxx
        self.defaultvals = {} # (public) ###doc, ####@@@@ use more, also know is_mutable about them, maybe more policy about del on copy
        self.warn = True # from decls seen so far, do we need to warn about this class (once, when we encounter it)?
        self.debug_all_attrs = False # was env.debug(); can normally be False now that system works
        
        self._find_attr_decls(class1) # fills self.policies and some other instance variables derived from them

        self.attrs_with_no_dflt = tuple(self.attrs_with_no_dflt) # optimization, I presume; bad if we let new attrs get added later
        self.attr_dflt_pairs = tuple(self.attr_dflt_pairs)
        
        self.S_CHILDREN_attrs = self.attrs_declared_as(S_CHILD) + self.attrs_declared_as(S_CHILDREN) #e sorted somehow? no need yet.
        self._objs_are_data = copiers_for_InstanceType_class_names.has_key(class1.__name__) or hasattr(class1, '_s_deepcopy')

        if self.warn and env.debug():
            # note: this should not be env.debug() since anyone adding new classes needs to see it...
            # but during development, with known bugs like this, we should not print stuff so often...
            # so it's env.debug for now, ####@@@@ FIX THAT LATER  [060227]
            print "InstanceClassification for %r sees no mixin or _s_attr decls; please add them or register it (nim)" \
                  % class1.__name__
        return

    def __repr__(self):
        return "<%s at %#x for %s>" % (self.__class__.__name__, id(self), self.class1.__name__)
    
    def _find_attr_decls(self, class1):
        "find _s_attr_xxx decls on class1, and process/store them"
        if self.debug_all_attrs:
            print "debug: _find_attr_decls in %s:" % (class1.__name__,)
        hmm = filter(lambda x: x.startswith("_s_"), dir(class1))
        for name in hmm:
            if name.startswith('_s_attr_'):
                attr_its_about = name[len('_s_attr_'):]
                declval = getattr(class1, name)
                self.policies[attr_its_about] = declval #k for class1, not in general
                if self.debug_all_attrs:
                    print "  %s = %s" % (name, declval)
                self.warn = False # enough to be legitimate state
                #e check if per-instance? if callable? if legal?
                if declval in STATE_ATTR_DECLS:
                    self.dict_of_all_state_attrs[attr_its_about] = None
                    # figure out if this attr has a known default value... in future we'll need decls to guide/override this
                    try:
                        dflt = getattr(class1, attr_its_about)
                    except AttributeError:
                        # assume no default value unless one is declared (which is nim)
                        self.attrs_with_no_dflt.append(attr_its_about)
                    else:
                        self.attr_dflt_pairs.append( (attr_its_about, dflt) )
                        self.defaultvals[attr_its_about] = dflt
                        #e maybe also test dflt for is_mutable (nim)?
                        if self.debug_all_attrs:
                            print "                                               dflt val for %r is %r" % (attr_its_about, dflt,)
                    pass
                pass
            elif name.startswith('_s_deepcopy_'):
                self.warn = False # enough to be legitimate data
            elif name.startswith('_s_scan_children_'):
                pass ## probably not: self.warn = False
            elif name.startswith('_s_categorize_'): #060227
                attr_its_about = name[len('_s_categorize_'):]
                declval = getattr(class1, name)
                assert type(declval) == type('category') # not essential, just to warn of errors in initial planned uses
                self.categories[attr_its_about] = declval
            else:
                print "warning: unrecognized _s_ attribute ignored:", name ##e
        return

    def attrs_declared_as(self, S_something):
        #e if this is commonly called, we'll memoize it in __init__ for each S_something
        res = []
        for attr, decl in self.policies.iteritems():
            if decl == S_something:
                res.append(attr)
        return res

    def obj_is_data(self, obj):
        "Should obj (one of our class's instances) be considered a data object?"
        return self._objs_are_data ## or hasattr(obj, '_s_deepcopy'), if we let individual instances override their classes on this
    
    def copy(self, val, func): # from outside, when in vals, it might as well be atomic! WRONG, it might add self to todo list...
        "Copy val, a (PyObject pointer to an) instance of our class"
        return val
    
##    def delve(self, val): #e rename -- more than one way to delve, probably
##        "Delve into val, an instance of our class"
##        #e grab our declared attrs in some order... maybe also look in val.__dict__... btw is val already registered with a key?
##        # might need another arg which is the archive for that

    def scan_children( self, obj1, func, deferred_category_collectors = {}):
        "[for #doc of deferred_category_collectors, see caller docstring]"
        try:
            # (we might as well test this on obj1 itself, since not a lot slower than memoizing the same test on its class)
            method = obj1._s_scan_children # bug: not yet passing deferred_category_collectors ###@@@ [not needed for A7, I think]
        except AttributeError:
            for attr in self.S_CHILDREN_attrs:
                val = getattr(obj1, attr, None)
                cat = self.categories.get(attr) #e need to optimize this (separate lists of attrs with each cat)?
                # cat is usually None; following code works then too;
                #e future optim note: often, cat is 'selection' but val contains no objects (for attr 'picked', val is boolean)
                collector = deferred_category_collectors.get(cat) # either None, or a dict we should modify (perhaps empty now)
                if collector is not None: # can't use boolean test, since if it's {} we want to use it
                    def func2(obj):
                        ## print "collecting %r into %r while scanning %r" % (obj, cat, attr) # works [060227]
                        collector[id(obj)] = obj
                    scan_val(val, func2)
                else:
                    scan_val(val, func) # don't optimize for val is None, since it's probably rare, and this is pretty quick anyway
                #e we might optimize by inlining scan_val, though
        else:
            method(func)
        return

    pass # end of class InstanceClassification

# == helper code  [##e all code in this module needs reordering]

known_type_copiers = {} # needs no entry for types whose instances can all be copied as themselves

known_type_scanners = {} # only needs entries for types whose instances might contain (or be) InstanceType objects,
    # and which might need to be entered for finding "children" (declared with S_CHILD) -- for now we assume that means
    # there's no need to scan inside bound method objects, though this policy might change.

# not yet needed, but let the variable exist since there's one use of it I might as well leave active (since rarely run):
copiers_for_InstanceType_class_names = {} # copier functions for InstanceTypes whose classes have certain names
    # (This is mainly for use when we can't add methods to the classes themselves.
    #  The copiers should verify the class is the expected one, and return the original object unchanged if not
    #  (perhaps with a warning), or raise an exception if they "own" the classname.)

# scanners_for_class_names would work the same way, but we don't need it yet.

def copy_val(val): #bruce 060221 generalized semantics and rewrote for efficiency
    """Efficiently copy a general Python value (so that mutable components are not shared with the original),
    passing Python instances unchanged, unless they define a _s_deepcopy method,
    and passing unrecognized objects (e.g. QWidgets, bound methods) through unchanged.
       (See a code comment for the reason we can't just use the standard Python copy module for this.)
    """
    typ = type(val)
    copier = known_type_copiers.get(typ) # this is a fixed public dictionary
    if copier is not None:
        return copier(val) # we optimize by not storing any copier for atomic types.
    return val

def scan_val(val, func): 
    """Efficiently scan a general Python value, and call func on all InstanceType objects encountered
    (or in the future, on objects of certain other types, like registered new-style classes or extension classes).
       No need to descend inside any values unless they might contain InstanceType objects. Note that some InstanceType
    objects define the _s_scan_children method, but we *don't* descend into them here using that -- this is only done
    by other code, such as whatever code func might end up delivering such objects to.
       Special case: we never descend into bound method objects either (see comment on known_type_scanners
    for why).
       Return an arbitrary value which caller should not use (always None in the present implem).
    """
    typ = type(val)
    scanner = known_type_scanners.get(typ) # this is a fixed public dictionary
    if scanner is not None:
        scanner(val, func) # we optimize by not storing any scanner for atomic types, or a few others.
    return

known_type_copiers[type([])] = copy_list
known_type_copiers[type({})] = copy_dict
known_type_copiers[type(())] = copy_tuple

known_type_scanners[type([])] = scan_list
known_type_scanners[type({})] = scan_dict
known_type_scanners[type(())] = scan_tuple

def copy_InstanceType(obj): #e pass copy_val as an optional arg?
    # note: this shares some code with InstanceClassification  ###@@@DOIT
    # not yet needed, since QColor is not InstanceType (but keep the code here for when it is needed):
    ##copier = copiers_for_InstanceType_class_names.get(obj.__class__.__name__)
    ##    # We do this by name so we don't need to import QColor (for example) unless we encounter one.
    ##    # Similar code might be needed by anything that looks for _s_deepcopy (as a type test or to use it). ###@@@ DOIT, then remove cmt
    ##    #e There's no way around checking this every time, though we might optimize
    ##    # by storing specific classes which copy as selves into some dict;
    ##    # it's not too important since we'll optimize Atom and Bond copying in other ways.
    ##if copier is not None:
    ##    return copier(obj, copy_val) # e.g. for QColor
    try:
        deepcopy_method = obj._s_deepcopy # note: not compatible with copy.deepcopy's __deepcopy__ method
    except AttributeError:
        return obj
    res = deepcopy_method( copy_val)
    if obj != res or (not (obj == res)):
        # Bug in deepcopy_method, which will cause false positives in change-detection in Undo (since we'll return res anyway).
        # (It's still better to return res than obj, since returning obj could cause Undo to completely miss changes.)
        #
        # Note: we require obj == res, but not res == obj (e.g. in case a fancy number turns into a plain one).
        # Hopefully the fancy object could define some sort of __req__ method, but we'll try to not force it to for now;
        # this has implications for how our diff-making archiver should test for differences. ###@@@doit
        print "bug: obj != res or (not (obj == res)), where res is _s_deepcopy of obj; obj is %r and res is %r" % (obj, res)
        #e also print history redmsg, once per class per session?
    return res

known_type_copiers[ types.InstanceType ] = copy_InstanceType

def scan_InstanceType(obj, func):
    func(obj)
    #e future optim: could we change API so that apply could serve in place of scan_InstanceType?
    # Probably not, but nevermind, we'll just do all this in C.
    return None 

known_type_scanners[ types.InstanceType ] = scan_InstanceType

# ==

def copy_Numeric_array(obj):
    if obj.typecode() == PyObject:
        if env.debug():
            print "atom_debug: ran copy_Numeric_array, PyObject case" # remove when works once ###@@@
        return array( map( copy_val, obj) )
            ###e this is probably incorrect for multiple dimensions; doesn't matter for now.
            # Note: We can't assume the typecode of the copied array should also be PyObject,
            # since _s_deepcopy methods could return anything, so let it be inferred.
            # In future we might decide to let this typecode be declared somehow...
##    if env.debug():
##        print "atom_debug: ran copy_Numeric_array, non-PyObject case" # remove when works once ... it did
    return obj.copy() # use Numeric's copy method for Character and number arrays ###@@@ verify ok from doc of this method...

def scan_Numeric_array(obj, func):
    if obj.typecode() == PyObject:
        if env.debug():
            print "atom_debug: ran scan_Numeric_array, PyObject case" # remove when works once ###@@@
        map( func, obj)
        # is there a more efficient way?
        ###e this is probably incorrect for multiple dimensions; doesn't matter for now.
    if env.debug():
        print "atom_debug: ran copy_Numeric_array, yes-or-non-PyObject case" # remove when works once for non- ###@@@
    return

try:
    from Numeric import array, PyObject
except:
    if env.debug():
        print "fyi: can't import array, PyObject from Numeric, so not registering its copy & scan functions"
else:
    numeric_array_type = type(array(range(2))) # __name__ is 'array', but Numeric.array itself is a built-in function, not a type
    assert numeric_array_type != types.InstanceType
    known_type_copiers[ numeric_array_type ] = copy_Numeric_array
    known_type_scanners[ numeric_array_type ] = scan_Numeric_array
    del numeric_array_type # but leave array, PyObject as module globals for use by the functions above, for efficiency
    pass

# ==

def copy_QColor(obj):
    from qt import QColor
    assert obj.__class__ is QColor # might fail (in existing calls) if some other class has the same name
    if env.debug():
        print "atom_debug: ran copy_QColor" # remove when works once; will equality work right? ###@@@
    return QColor(obj)

try:
    # this is the simplest way to handle QColor for now; if always importing qt from this module
    # becomes a problem (e.g. if this module should work in environments where qt is not available),
    # make other modules register QColor with us, or make sure it's ok if this import fails
    # (it is in theory).
    from qt import QColor
except:
    if env.debug():
        print "fyi: can't import QColor from qt, so not registering its copy function"
else:
    QColor_type = type(QColor())
        # note: this is the type of a QColor instance, not of the class!
        # type(QColor) is <type 'sip.wrappertype'>, which we'll just treat as a constant,
        # so we don't need to handle it specially.
    assert QColor_type != types.InstanceType
    ## wrong: copiers_for_InstanceType_class_names['qt.QColor'] = copy_QColor
    known_type_copiers[ QColor_type ] = copy_QColor
    # no scanner for QColor is needed, since it contains no InstanceType objects.
    del QColor, QColor_type
    pass

# ==

##e Do we need a copier function for a Qt event? Probably not, since they're only safe
# to store after making copies (see comments around QMouseEvent in selectMode.py circa 060220),
# and (by convention) those copies are treated as immutable.

# The reason we can't use the standard Python copy module's deepcopy function:
# it doesn't give us enough control over what it does to instances of unrecognized classes.
# For our own classes, we could do anything, but for other classes, we need them to be copied
# as the identity (i.e. as unaggressively as possible), or perhaps signalled as errors or warnings,
# but copy.deepcopy would copy everything inside them, i.e. copy them as aggressively as possible,
# and there appears to be no way around this.
#
##>>> import copy
##>>> class c:pass
##... 
##>>> c1 = c()
##>>> c2 = c()
##>>> print id(c1), id(c2)  
##270288 269568
##>>> c3 = copy.deepcopy(c1)
##>>> print id(c3)
##269968
#
# And what about the copy_reg module?... it's just a way of extending the Pickle module
# (which we also can't use for this), so it's not relevant.
#
# Notes for the future: we might use copy.deepcopy in some circumstances where we had no fear of
# encountering objects we didn't define;
# or we might write our own C/Pyrex code to imitate copy_val and friends.

# ==

# state_utils-copy_val-outtake.py went here, defined:
# class copy_run, etc
# copy_val

# ==

# state_utils-scanner-outtake.py went here, defined
# class attrlayer_scanner
# class scanner
# ##class Classifier: #partly obs? superseded by known_types?? [guess, 060221]
# ##the_Classifier = Classifier()

# ==

class objkey_allocator:
    """Use one of these to allocate small int keys for objects you're willing to keep forever.
    We provide public dict attrs with our tables, and useful methods for whether we saw an object yet, etc.
       Note: a main motivation for having these keys at all is speed and space when using them as dict keys in large dicts,
    compared to python id() values. Other motivations are their uniqueness, and possible use in out-of-session encodings,
    or in other non-live encodings of object references.
    """
    def __init__(self):
        self.obj4key = {}
            # maps key to object. this is intentionally not weak-valued. It's public.
        self._key4obj = {} # maps id(obj) -> key; semiprivate
        self._lastobjkey = 0

    def allocate_key(self, key = None): # not yet directly called; untested
        "Allocate the requested key (assertfail if it's not available), or a new one we make up, and store None for it."
        if key is not None:
            # this only makes sense if we allocated it before and then abandoned it (leaving a hole), which is NIM anyway,
            # or possibly if we use md5 or sha1 strings or the like for keys (though we'd probably first have to test for prior decl).
            # if that starts happening, remove the assert 0.
            assert 0, "this feature should never be used in current code (though it ought to work if it was used correctly)"
            assert not self.obj4key.has_key(key)
        else:
            # note: this code also occurs directly in key4obj_maybe_new, for speed
            self._lastobjkey += 1
            key = self._lastobjkey
            assert not self.obj4key.has_key(key) # different line number than identical assert above (intended)
        self.obj4key[key] = None # placeholder; nothing is yet stored into self._key4obj, since we don't know obj!
        return key

    def key4obj(self, obj): # maybe not yet directly called; untested
        """What's the key for this object, if it has one? Return None if we didn't yet allocate one for it.
        Ok to call on objects for which allocating a key would be illegal (in fact, on any Python values, I think #k).
        """
        return self._key4obj.get(id(obj)) #e future optim: store in the obj, for some objs? not sure it's worth the trouble,
            # except maybe in addition to this, for use in inlined code customized to the classes. here, we don't need to know.
            # Note: We know we're not using a recycled id since we have a ref to obj! (No need to test it -- having it prevents
            # that obj's id from being recycled. If it left and came back, this is not valid, but then neither would the comparison be!)

    def key4obj_maybe_new(self, obj):
        """What's the key for this object, which we may not have ever seen before (in which case, make one up)?
        Only legal to call when you know it's ok for this obj to have a key (since this method doesn't check that).
        Optimized for when key already exists.
        """
        try:
            return self._key4obj[id(obj)]
        except KeyError:
            pass
        # this is the usual way to assign new keys to newly seen objects (maybe the only way)
        # note: this is an inlined portion of self.allocate_key()
        self._lastobjkey += 1
        key = self._lastobjkey
        assert not self.obj4key.has_key(key)
        self.obj4key[key] = obj
        self._key4obj[id(obj)] = key
        return key
    
    pass # end of class objkey_allocator

# ==

class StateSnapshot:
    """A big pile of saved (copies of) attribute values -- for each known attr, a dict from objkey to value.
    The code that stores data into one of these is the collect_state method in some other class.
    The code that applies this data to live current objects is... presently in assy_become_scanned_state
    but maybe should be a method in this class. ####@@@@
    """
    #e later we'll have one for whole state and one for differential state and decide if they're different classes, etc
    def __init__(self, attrs = ()):
        self.attrdicts = {} # maps attrnames to their dicts; each dict maps objkeys to values; public attribute for efficiency(??)
        for attr in attrs:
            self.make_attrdict(attr)
    #e methods to apply the data and to help grab the data? see also assy_become_scanned_state, SharedDiffopData (in undo_archive)
    #e future: methods to read and write the data, to diff it, etc, and state-decls to let it be compared...
    #e will __eq__ just be eq on our attrdicts? or should attrdict missing or {} be the same? guess: same.
    def make_attrdict(self, attr):
        "Make an attrdict for attr. Assume we don't already have one."
        assert self.attrdicts.get(attr) is None
        self.attrdicts[attr] = {}
    def size(self): ##e should this be a __len__ and/or a __nonzero__ method?
        "return the total number of attribute values we're storing (over all objects and all attrnames)"
        res = 0
        for d in self.attrdicts.values():
            # <rant> Stupid Python didn't complain when I forgot to say .values(),
            # but just told me how many letters were in all the attrnames put together! </rant>
            # (Iteration over a dict being permitted is bad enough (is typing .items() so hard?!?),
            #  but its being over the keys rather than over the values is even worse. IMO.)
            res += len(d)
        return res
    def __str__(self):
        return "<%s at %#x, %d attrdicts, %d total values>" % (self.__class__.__name__, id(self), len(self.attrdicts), self.size())
##    def print_value_stats(self): # debug function, not yet needed
##        for d in self.attrdicts:
##            # (attrname in more than one class is common, due to inheritance)
##            pass # not yet needed now that I fixed the bug in self.size(), above
    def __eq__(self, other):
        "[this is used by undo_archive to see if the state has really changed]"
        # this implem assumes modtimes/change_counters are not stored in the snapshots (or, not seen by diff_snapshots)!
        return self.__class__ is other.__class__ and not diff_snapshots(self, other)
    def __ne__(self, other):
        return not (self == other)
    pass # end of class StateSnapshot

def diff_snapshots(snap1, snap2): #060227 experimental
    "Diff two snapshots. Retval format TBD. Missing attrdicts are like empty ones. obj/attr sorting by varid to be added later."
    keydict = dict(snap1.attrdicts) # shallow copy, used only for its keys (presence of big values shouldn't slow this down)
    keydict.update(snap2.attrdicts)
    attrs = keydict.keys()
    del keydict
    attrs.sort() # just so we're deterministic
    res = {}
    for attr in attrs:
        d1 = snap1.attrdicts.get(attr, {})
        d2 = snap2.attrdicts.get(attr, {})
        # now diff these dicts; set of keys might not be the same
        dflt = _UNSET_
            # This might be correct, assuming each attrdict has been optimized to not store true dflt val for attrdict,
            # or each hasn't been (i.e. same policy for both).
            # Needs review. ##k ###@@@ [060227 comment]
        diff = diffdicts(d1, d2, dflt)
        if diff:
            res[attr] = diff #k ok not to copy its mutable state? I think so...
    return res # just a diff-attrdicts-dict, with no empty dict members (so boolean test works ok) -- not a Snapshot itself.

def diffdicts(d1, d2, dflt = None): ###e dflt is problematic since we don't know it here and it might vary by obj or class
    """Given two dicts, return a new one with entries at keys where their values differ (according to ==),
    treating missing values as dflt. Values in retval are pairs (v1, v2) where v1 = d1.get(key, dflt), and same for v2.
    WARNING: v1 and v2 and dflt in these pairs are not copied; retval might share mutable state with d1 and d2 values and dflt arg.
    """
    ###E maybe this dflt feature is not needed, if we already didn't store vals equal to dflt? but how to say "unset" in retval?
    # Do we need a new unique object not equal to anything else, just to use for Unset?
    res = {}
    for key, v1 in d1.iteritems():
        v2 = d2.get(key, dflt)
        if v1 == v2: # optim: == will be faster than != for some of our most common values
            pass
        else:
            res[key] = (v1,v2)
    for key, v2 in d2.iteritems():
        #e (optim note: i don't know how to avoid scanning common keys twice, just to find d2-only keys;
        #   maybe copying d1 and updating with d2 and scanning that would be fastest way?)
        # if d1 has a value, we handled this key already, and this is usually true, so test that first.
        if not d1.has_key(key):
            v1 = dflt
            if v1 == v2: # same order and test as above
                pass
            else:
                res[key] = (v1,v2)
    return res
        
# ==

# Terminology/spelling note: in comments, we use "class" for python classes, "clas" for Classification objects.
# In code, we can't use "class" as a variable name (since it's a Python keyword),
# so we might use "clas" (but that's deprecated since we use it for Classification objects too),
# or "class1", or something else.

class obj_classifier: 
    """Classify objects seen, and save the results, and provide basic uses of the results for scanning.
    Probably can't yet handle "new-style" classes. Doesn't handle extension types (presuming they're not InstanceTypes) [not sure].
    """
    def __init__(self):
        self._clas_for_class = {} # maps Python classes (values of obj.__class__ for obj an InstanceType, for now) to Classifications
        self.dict_of_all_state_attrs = {} # maps attrnames to arbitrary values, for all state-holding attrnames ever declared to us
        self.kluge_attr2metainfo = {}
            # maps attrnames to the only legal attr_metainfo for that attrname; the kluge is that we require this to be constant per-attr
        self.kluge_attr2metainfo_from_class = {}
        return
    
    def classify_instance(self, obj):
        """Obj is known to be of types.InstanceType. Classify it (memoizing classifications per class when possible).
        It might be a StateHolder, Data object, or neither.
        """
        class1 = obj.__class__
        try:
            # easy case: we know that __class__ (and it doesn't need to be redone per-object, which anyway is nim)
            # (this is probably fast enough that we don't need to bother storing a map from id(obj) or objkey directly to clas,
            #  which might slow us down anyway by using more memory)
            # (#e future optim, though: perhaps store clas inside the object, and also objkey, as special attrs)
            return self._clas_for_class[class1]
        except:
            pass
        # make a new Classification for this class
        clas = self._clas_for_class[class1] = InstanceClassification(class1)
        self.dict_of_all_state_attrs.update( clas.dict_of_all_state_attrs )
        # Store per-attrdict metainfo, which in principle could vary per-class but should be constant for one attrdict.
        # This means that classes that disagree about metainfo for the same attrname would need to encode attrnames
        # into distinct attrkeys to use when finding attrdicts.
        # Right now we know that never happens, so we just assert it doesn't.
        #e (To make this system more general (after A7) we'll need to remove assumption that attrname is the right index
        #   for finding the attrdict. E.g. attr_dflt_pairs becomes (attr, attrkey, dflt) triples, etc.
        #   Then the following code would need to say it would:
        #      Figure out whether there's any problematic attrname conflicts that mean we need to encode attrnames,
        #      so that different classes use different attrdicts for the same-named attr.
        # )

        # BTW this metainfo is needed by StateSnapshot methods and external code... review organization of all this code later.

        for attr in clas.dict_of_all_state_attrs.keys():
            attr_metainfo = (attr, clas.defaultvals.get(attr, _UNSET_), clas.categories.get(attr)) #e make this a clas method?
            if self.kluge_attr2metainfo.has_key(attr):
                if self.kluge_attr2metainfo[attr] != attr_metainfo:
                    #060228 be gentler, since happens for e.g. Jig.color attrs; collect cases, then decide what to do
                    if self.kluge_attr2metainfo[attr][1] != attr_metainfo[1]:
                        msg = "undo-debug note: attr %r defaultval differs in %s and %s; ok for now but mention in bug 1586 comment" % \
                              (attr, class1.__name__, self.kluge_attr2metainfo_from_class[attr].class1.__name__)
                        print msg
                        from HistoryWidget import redmsg
                        env.history.message(redmsg( msg ))
                        attr_metainfo = list(attr_metainfo)
                        attr_metainfo[1] = self.kluge_attr2metainfo[attr][1] # look the other way - ok since not using this yet ###@@@
                        attr_metainfo = tuple(attr_metainfo)
                assert self.kluge_attr2metainfo[attr] == attr_metainfo, \
                        "%r == %r fails for %r (2nd class is %s, 1st clas incls %r)" % \
                        (self.kluge_attr2metainfo[attr], attr_metainfo,
                         attr, class1.__name__, self.kluge_attr2metainfo_from_class[attr].class1.__name__ )
                    # require same-named attrs to have same dflt and cat (for now) -- no, dflt can differ, see above kluge ###@@@
            else:
                self.kluge_attr2metainfo[attr] = attr_metainfo
                self.kluge_attr2metainfo_from_class[attr] = clas # only for debugging
        return clas

    def metainfo4attrkey(self, attrkey): #060227; intended for use in upcoming code to diff snaps and know what kind of state changed.
        "Return (attrname, defaultval, category) for the given attrkey. (Kluge: for now attrkey == attrname.)"
        # Someday attrkeys won't always equal attrnames. This API can still work then, tho implem won't.
        return self.kluge_attr2metainfo[attrkey]
    
    def collect_s_children(self, val, deferred_category_collectors = {}):
        """Collect all objects in val, and their s_children, defined as state-holding objects
        found (recursively, on these same objects) in their attributes which were
        declared S_CHILD or S_CHILDREN using the state attribute decl system... [#doc that more precisely]
        return them as the values of a dictionary whose keys are their python id()s.
           Note: this scans through "data objects" (defined as those which define an '_s_deepcopy' method)
        only once, but doesn't include them in the return value. This is necessary (I think) because
        copy_val copies such objects. (Whether it's optimal is not yet clear.)
           If deferred_category_collectors is provided, it should be a dict from attr-category names
        (e.g. 'selection', 'view') to usually-empty dicts, into which we'll store id/obj items
        which we reach through categorized attrs whose category names it lists, rather than scanning them
        recursively as usual. If we reach one object along multiple attr-paths with different categories,
        we decide what to do independently each time (thus perhaps recursivly scanning the same object
        we store in a dict in deferred_category_collectors, or storing it in more than one of those dicts).
        Caller should ignore such extra object listings as it sees fit. 
        """ 
        #e optimize for hitting some children lots of times, by first storing on id(obj), only later looking up key (if ever).
        saw = {}
        def func(obj):
            saw[id(obj)] = obj
        scan_val(val, func)
        # now we have some objects to classify and delve into.
        # for each one, we call this (more or less) on val of each child attribute.
        # but we need to do this in waves so we know when we're done. and not do any obj twice.
        # (should we detect cycles of children, which is presumably an error? not trivial to detect, so no for now.)
        # ... this is just transitive closure in two steps, obj to some vals, and those vals scanned (all together).
        # So write the obj to "add more objs to a dict" func. then pass it to a transclose utility, which takes care
        # of knowing which objs are seen for first time.
        data_objs = {}
        def obj_and_dict(obj1, dict1): #e rename
            """pass me to transclose; I'll store objs into dict1 when I reach them from a child attribute of obj; all objs are
            assumed to be instances of the kind acceptable to classify_instance.
            """
            # note, obj1 might be (what we consider) either a StateHolder or a Data object (or neither).
            # Its clas will know what to do.
            clas = self.classify_instance(obj1)
            if clas.obj_is_data(obj1):
                data_objs[id(obj1)] = obj1
            def func(obj):
                dict1[id(obj)] = obj
            clas.scan_children( obj1, func, deferred_category_collectors = deferred_category_collectors)
        allobjs = transclose( saw, obj_and_dict) #e rename both args
        if 0 and env.debug(): ###e remove after debugging
            print "atom_debug: collect_s_children had %d roots, from which it reached %d objs, of which %d were data" % \
                  (len(saw), len(allobjs), len(data_objs))
        # allobjs includes both state-holding and data-holding objects. Remove the latter.
        for key in data_objs.iterkeys():
            del allobjs[key]
        return allobjs # from collect_s_children

    def collect_state(self, objdict, keyknower):
        """Given a dict from id(obj) to obj, which is already transclosed to include all objects of interest,
        ensure all these objs have objkeys (allocating them from keyknower (an objkey_allocator instance) as needed),
        and grab the values of all their state-holding attrs,
        and return this in the form of a StateSnapshot object.
        #e In future we'll provide a differential version too.
        """
        key4obj = keyknower.key4obj_maybe_new # or our arg could just be this method
        snapshot = StateSnapshot(self.dict_of_all_state_attrs.keys())
            # make a place to keep all the values we're about to grab
        attrdicts = snapshot.attrdicts
        for obj in objdict.itervalues():
            key = key4obj(obj)
            clas = self.classify_instance(obj)
            # hmm, use attrs in clas or use __dict__? Either one might be way too big... start with smaller one? nah. guess.
            # also we might as well use getattr and be more flexible (not depending on __dict__ to exist). Ok, use getattr.
            # Do we optim dflt values of attrs? We ought to... even when we're differential, we're not *always* differential.
            ###e need to teach clas to know those, then.
            for attr, dflt in clas.attr_dflt_pairs: # for attrs holding state (S_DATA, S_CHILD*, S_PARENT*, S_REF*) with dflts
                val = getattr(obj, attr, dflt)
                if val is not dflt: # it's important in general to use 'is' rather than '==' (I think), e.g. for different copies of {}
                    # We might need to store a copy of val, or we might not if val == dflt and it's not mutable.
                    # There's no efficient perfect test for this, and it's not worth the runtime to even guess it,
                    # since for typical cases where val needn't be stored, val is dflt since instance didn't copy it.
                    # (Not true if Undo stored the val back into the object, but it won't if it doesn't copy it out!)
                    attrdicts[attr][key] = copy_val(val)
            for attr in clas.attrs_with_no_dflt:
                # (This kind of attr might be useful when you want full dicts for turning into Numeric arrays later. Not sure.)
                # Does that mean the attr must always exist on obj? Or that we should "store its nonexistence"?
                # For simplicity, I hope latter case can always be thought of as the attr having a default.
                # I might need a third category of attrs to pull out of __dict__.get so we don't run __getattr__ for them... ##e
                #val = getattr(obj, attr)
                #valcopy = copy_val(val)
                #attrdict = attrdicts[attr]
                #attrdict[key] = valcopy
                attrdicts[attr][key] = copy_val(getattr(obj, attr))
                    # We do it all in one statement, for efficiency in case compiler is not smart enough to see that local vars
                    # would not be used again; it might even save time due to lack of bytecodes to update linenumber
                    # to report in exceptions! (Though that will make bugs harder to track down, if exceptions occur.)
        if 0 and env.debug():
            print "atom_debug: collect_state got this snapshot:", snapshot
##            if 1: #####@@@@@
##                snapshot.print_value_stats() # NIM
        return snapshot

    def reset_obj_attrs_to_defaults(self, obj):
        """Given an obj we have saved state for, reset each attr we might save
        to its default value (which might be "missing"??), if it has one.
        [#e someday we might also reset S_CACHE attrs, but not for now.]
        """
        clas = self.classify_instance(obj)
        for attr, dflt in clas.attr_dflt_pairs:
            setattr(obj, attr, copy_val(dflt)) #e need copy_val?
            #e save this for when i have time to analyze whether it's safe:
            ## delattr(obj, attr) # save RAM -- ok (I think) since the only way we get dflts is when this would work... not sure
        # not needed: for attr in clas.attrs_with_no_dflt: ...
        return
    
    pass # end of class obj_classifier, if we didn't rename it by now

# ==

class StateMixin( _eq_id_mixin_ ):
    """Convenience mixin for classes that contain state-attribute decls,
    to help them follow the rules for __eq__,
    to avoid debug warnings when they contain no attr decls yet,
    and perhaps to provide convenience methods (none are yet defined).
    """
    # try not having this:
    ## _s_attr__StateMixin__fake = S_IGNORE
        # decl for fake attr __fake (name-mangled to _StateMixin__fake to be private to this mixin class),
        # to avoid warnings about classes with no declared state attrs without requiring them to be registered (which might be nim)
        # (which is ok, since if you added this mixin to them, you must have thought about
        #  whether they needed such decls)
    def _undo_update(self):
        "#doc [see docstring in chunk]"
        return
    pass

class DataMixin:
    """Convenience mixin for classes that act as "data" when present
    in values of declared state-holding attributes. Provides method stubs
    to remind you when you haven't declared a necessary method. (not sure this is good)
    Makes sure state system treats this object as data (and doesn't warn about it).
    """
    def _s_deepcopy(self, copyfunc): # note: presence of this method makes sure this object is treated as data.
        "#doc [doc available in other implems of this method, and/or its calls; implem must be compatible with __eq__]"
        print "_s_deepcopy needs to be overridden in", self
        print "  (implem must be compatible with __eq__)"
        return self
    def __eq__(self, other):
        print "__eq__ needs to be overridden in", self ### don't put this mixin into Gamess til I test lack of __eq__ there
        print "  (implem must be compatible with _s_deepcopy)"
        return self is other
    def __ne__(self, other):
        return not (self == other) # this uses the __eq__ above, or one which the main class defined
    pass

# == test code

def _test():
    print "testing some simple cases of copy_val"
    from Numeric import array
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
