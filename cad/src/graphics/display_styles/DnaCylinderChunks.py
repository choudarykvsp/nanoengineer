# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaCylinderChunks.py -- defines I{DNA Cylinder} display mode, which draws 
axis chunks as a cylinder in the chunk's color.

@author: Mark
@version: $Id$
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details. 

This is still considered experimental.

Initially, this is mainly intended as a fast-rendering display mode for DNA.
When the DNA data model become operative, this class will be implemented
to give faster and better ways to compute the axis path and render the
cylinder.

To do:
- Add new user pref for "DNA Cylinder Radius".
- Fix limitations/bugs listed in the class docstring.

History:
Mark 2008-02-12: Created by making a copy of CylinderChunks.py
"""

from Numeric import dot, argmax, argmin, sqrt

import foundation.env as env
import graphics.drawing.drawer as drawer
from geometry.geometryUtilities import matrix_putting_axis_at_z
from geometry.VQT import V, norm
from debug import print_compact_traceback
from graphics.display_styles.displaymodes import ChunkDisplayMode
from constants import ave_colors, red
from prefs_constants import atomHighlightColor_prefs_key
from model.elements import Singlet

chunkHighlightColor_prefs_key = atomHighlightColor_prefs_key # initial kluge

class DnaCylinderChunks(ChunkDisplayMode):
    """
    DNA Cylinder display mode, which draws "axis" chunks as a cylinder.
    
    Limitations/known bugs:
    - Cylinders are always straight. DNA axis chunks with atoms that are not 
    aligned in a straight line are not displayed correctly (i.e. they don't
    follow a curved axis path.
    - Hover highlighting does not work.
    - Selected chunks are not colored in the selection color.
    - Cannot drag/move a selected cylinder interactively.
    - DNA Cylinders are not written to POV-Ray file.
    - DNA Cylinders are not written to PDB file and displayed in QuteMolX.

    @note: Nothing else is rendered (no atoms, sugar atoms, etc) when 
        set to this display mode.
                
    @attention: This is still considered experimental.
    """
    # mmp_code must be a unique 3-letter code, distinct from the values in 
    # constants.dispNames or in other display modes
    mmp_code = 'dna'  
    disp_label = 'DNA Cylinder' # label for statusbar fields, menu text, etc.
    featurename = "Set Display DNA Cylinder"
    # Pretty sure Bruce's intention is to define icons for subclasses
    # of ChunkDisplayMode here, not in mticon_names[] and hideicon_names[] 
    # in chunks.py. Ask him to be sure. Mark 2008-02-12
    icon_name = "modeltree/DnaCylinder.png"
    hide_icon_name = "modeltree/DnaCylinder-hide.png"
    ##e also should define icon as an icon object or filename, either in class or in each instance
    ##e also should define a featurename for wiki help
    def drawchunk(self, glpane, chunk, memo, highlighted):
        """
        Draw chunk in glpane in the whole-chunk display mode represented by 
        this ChunkDisplayMode subclass.
        
        Assume we're already in chunk's local coordinate system (i.e. do all
        drawing using atom coordinates in chunk.basepos, not chunk.atpos).
        
        If highlighted is true, draw it in hover-highlighted form (but note 
        that it may have already been drawn in unhighlighted form in the same
        frame, so normally the highlighted form should augment or obscure the
        unhighlighted form).
        
        Draw it as unselected, whether or not chunk.picked is true. See also
        self.drawchunk_selection_frame. (The reason that's a separate method
        is to permit future drawing optimizations when a chunk is selected
        or deselected but does not otherwise change in appearance or position.)
        
        If this drawing requires info about chunk which it is useful to 
        precompute (as an optimization), that info should be computed by our
        compute_memo method and will be passed as the memo argument
        (whose format and content is whatever self.compute_memo returns). 
        That info must not depend on the highlighted variable or on whether
        the chunk is selected.
        """
        
        if not memo:
            return
        if not chunk.atoms:
            # This should never happen since compute_memo() already checks this.
            # Ask Bruce is I'm correct. Mark 2008-02-12
            return 
        end1, end2, radius, color = memo
        if highlighted:
            color = ave_colors(0.5, color, env.prefs[chunkHighlightColor_prefs_key]) #e should the caller compute this somehow?
        drawer.drawcylinder(color, end1, end2, radius, capped = True)
        return
    def drawchunk_selection_frame(self, glpane, chunk, selection_frame_color, memo, highlighted):
        """
        Given the same arguments as drawchunk, plus selection_frame_color, 
        draw the chunk's selection frame.
        
        (Drawing the chunk itself as well would not cause drawing errors
        but would presumably be a highly undesirable slowdown, especially if
        redrawing after selection and deselection is optimized to not have to
        redraw the chunk at all.)
        
        @note: in the initial implementation of the code that calls this method,
        the highlighted argument might be false whether or not we're actually
        hover-highlighted. And if that's fixed, then just as for drawchunk, 
        we might be called twice when we're highlighted, once with 
        highlighted = False and then later with highlighted = True.
        """
        if not chunk.atoms:
            return
        end1, end2, radius, color = memo
        color = selection_frame_color
        # make it a little bigger than the cylinder itself
        axis = norm(end2 - end1)
        alittle = 0.01
        end1 = end1 - alittle * axis
        end2 = end2 + alittle * axis
        color = red
        drawer.drawcylinder_wireframe(color, end1, end2, radius + alittle)
        return
    
    def compute_memo(self, chunk):
        """
        If drawing chunks in this display mode can be optimized by precomputing
        some info from chunk's appearance, compute that info and return it.
        
        If this computation requires preference values, access them as 
        env.prefs[key], and that will cause the memo to be removed (invalidated)
        when that preference value is changed by the user.
        
        This computation is assumed to also depend on, and only on, chunk's
        appearance in ordinary display modes (i.e. it's invalidated whenever
        havelist is). There is not yet any way to change that, so bugs will 
        occur if any ordinarily invisible chunk info affects this rendering,
        and potential optimizations will not be done if any ordinarily visible
        info is not visible in this rendering. These can be fixed if necessary
        by having the real work done within class Chunk's _recompute_ rules,
        with this function or drawchunk just accessing the result of that
        (and sometimes causing its recomputation), and with whatever 
        invalidation is needed being added to appropriate setter methods of 
        class Chunk. If the real work can depend on more than chunk's ordinary
        appearance can, the access would need to be in drawchunk;
        otherwise it could be in drawchunk or in this method compute_memo().
        
        @param chunk: The chunk.
        @type  chunk: chunk
        """
        # for this example, we'll turn the chunk axes into a cylinder.
        # Since chunk.axis is not always one of the vectors chunk.evecs (actually chunk.poly_evals_evecs_axis[2]),
        # it's best to just use the axis and center, then recompute a bounding cylinder.
        if not chunk.atoms:
            return None
        for atom in chunk.atoms.itervalues():
            if not (atom.element.role == 'axis' or atom.element is Singlet):
                return None
        # WARNING: Any Singlets in the axis chunk will distort the (display)
        # length, axis and center. When the DNA data model is fully implemented,
        # this will need to be addressed somehow. Need Bruce's help with this.
        # Mark 2008-02-12
        axis = chunk.axis
        axis = norm(axis) # needed (unless we're sure it's already unit length, which is likely)
        center = chunk.center
        points = chunk.atpos - center # not sure if basepos points are already centered
        # compare following Numeric Python code to findAtomUnderMouse and its caller
        matrix = matrix_putting_axis_at_z(axis)
        v = dot( points, matrix)
        radius = 10.0 # This should become a user pref. Mark 2008-02-12
        # to get limits along axis (since we won't assume center is centered between them), use min/max z:
        z = v[:,2]
        min_z = z[argmin(z)]
        max_z = z[argmax(z)]
        bcenter = chunk.abs_to_base(center)
        # return, in chunk-relative coords, end1, end2, and radius of the cylinder, and color.
        color = chunk.color
        if color is None:
            color = V(0.5,0.5,0.5)
        # make sure it's longer than zero (in case of a single-atom chunk); in fact, add a small margin all around
        # (note: this is not sufficient to enclose all atoms entirely; that's intentional)
        margin = 0.2
        min_z -= margin
        max_z += margin
        radius += margin
        return (bcenter + min_z * axis, bcenter + max_z * axis, radius, color)
    pass # end of class DnaCylinderChunks

ChunkDisplayMode.register_display_mode_class(DnaCylinderChunks)

# end
