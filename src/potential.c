
#include "simulator.h"

// incremented each time either the potential or gradient is
// calculated.  Used to match values in bond->valid to determine the
// need to recalculate bond->inverseLength and bond->rUnit.
//
// This is the same as setting bond->valid to 0 for each bond,
// checking for non-zero, and setting to non-zero when calculated.  It
// doesn't require the reset loop at the start of each calculation,
// though.
//
// Probably should allow the use of the same serial number for back to
// back calls to potential and gradient using the same positions.  But
// then we'd have to save r and rSquared as well.
static int validSerial = 0;

// presumes that updateVanDerWaals() has been called already.
static void
setRUnit(struct xyz *position, struct bond *b, double *prSquared)
{
  struct xyz r;
  double rSquared;
  
  vsub2(r, position[b->a1->index], position[b->a2->index]);
  rSquared = vdot(r, r);
  b->inverseLength = 1.0 / sqrt(rSquared); /* XXX if atoms are on top of each other, 1/0 !! */
  vmul2c(b->rUnit, r, b->inverseLength); /* unit vector along r */
  if (prSquared) {
    *prSquared = rSquared;
  }
  b->valid = validSerial;
}

double
calculatePotential(struct part *p, struct xyz *position)
{
  int j;
  int k;
  double rSquared;
  double fac;
  struct xyz v1;
  struct xyz v2;
  double z;
  double theta;
  double ff;
  double potential = 0.0;

  /* interpolation */
  double *t1;
  double *t2;
  double start;
  int scale;

  struct interpolationTable *iTable;
  struct stretch *stretch;
  struct bond *bond;
  struct bond *bond1;
  struct bond *bond2;
  struct bend *bend;
  struct bendData *bType;
  double torque;
  struct vanDerWaals *vdw;
  struct xyz r;

  validSerial++;

  for (j=0; j<p->num_stretches; j++) {
    stretch = &p->stretches[j];
    bond = stretch->b;

    // we presume here that rUnit is invalid, and we need rSquared
    // anyway.
    setRUnit(position, bond, &rSquared);

    // table lookup equivalent to: fac = potentialLippincottMorse(rSquared);
    iTable = &stretch->stretchType->potentialLippincottMorse;
    start = iTable->start;
    scale = iTable->scale;
    t1 = iTable->t1;
    t2 = iTable->t2;
    k = (int)(rSquared - start) / scale;
    if (k < 0) {
      if (!ToMinimize && DEBUG(D_TABLE_BOUNDS)) { //linear
        fprintf(stderr, "stretch: low --");
        printStretch(stderr, p, stretch);
      }
      fac = t1[0] + rSquared * t2[0];
    } else if (k >= TABLEN) {
      if (ToMinimize) { // extend linearly past end of table
        fac = stretch->stretchType->potentialExtensionStiffness * rSquared
          + stretch->stretchType->potentialExtensionIntercept;
        //fac = t1[TABLEN-1]+ ((TABLEN-1) * scale + start) * t2[TABLEN-1];
      } else {
        fac=0.0;
        if (DEBUG(D_TABLE_BOUNDS)) {
          fprintf(stderr, "stretch: high --");
          printStretch(stderr, p, stretch);
        }
      }
    } else {
      fac = t1[k] + rSquared * t2[k];
    }
            
    potential += fac;
  }
			
  /* now the potential for each bend */
			
  for (j=0; j<p->num_bends; j++) {
    bend = &p->bends[j];

    bond1 = bend->b1;
    bond2 = bend->b2;

    // Update rUnit for both bonds, if necessary.  Note that we
    // don't need r or rSquared here.
    if (bond1->valid != validSerial) {
      setRUnit(position, bond1, NULL);
    }
    if (bond2->valid != validSerial) {
      setRUnit(position, bond2, NULL);
    }
      
    // v1, v2 are the unit vectors FROM the central atom TO the
    // neighbors.  Reverse them if we have to.
    if (bend->dir1) {
      vsetn(v1, bond1->rUnit);
    } else {
      vset(v1, bond1->rUnit);
    }
    if (bend->dir2) {
      vsetn(v2, bond2->rUnit);
    } else {
      vset(v2, bond2->rUnit);
    }

    // XXX figure out how close we can get / need to get.
    // we assume we only get this close to linear on actually linear
    // bonds, for which the potential should be zero at this point.
    if (-0.99 < vdot(v1,v2)) {

#define ACOS_POLY_A -0.0820599
#define ACOS_POLY_B  0.142376
#define ACOS_POLY_C -0.137239
#define ACOS_POLY_D -0.969476

      z = vlen(vsum(v1, v2));
      // this is the equivalent of theta=arccos(z);
      theta = Pi + z * (ACOS_POLY_D +
                   z * (ACOS_POLY_C +
                   z * (ACOS_POLY_B +
                   z *  ACOS_POLY_A   )));

      // XXX check that this is all ok...
      // bType->kb in yJ/rad^2 (1e-24 J/rad^2)
      bType = bend->bendType;
      torque = (theta - bType->theta0) * bType->kb;

      ff = torque * bond1->inverseLength;
      potential += ff * ff / 2.0;
      ff = torque * bond2->inverseLength;
      potential += ff * ff / 2.0;
    }
  }

  /* do the van der Waals/London forces */
  for (j=0; j<p->num_vanDerWaals; j++) {
    vdw = p->vanDerWaals[j];

    // The vanDerWaals array changes over time, and might have
    // NULL's in it as entries are deleted.
    if (vdw == NULL) {
      continue;
    }
      
    vsub2(r, position[vdw->a1->index], position[vdw->a2->index]);
    rSquared = vdot(r, r);
      
    /* table setup  */
    iTable = &vdw->parameters->potentialBuckingham;
    start = iTable->start;
    scale = iTable->scale;
    t1 = iTable->t1;
    t2 = iTable->t2;

    k=(int)(rSquared - start) / scale;
    if (k < 0) {
      if (!ToMinimize && DEBUG(D_TABLE_BOUNDS)) { //linear
        fprintf(stderr, "vdW: off table low -- r=%.2f \n",  sqrt(rSquared));
        printVanDerWaals(stderr, p, vdw);
      }
      k=0;
      fac = t1[k] + rSquared * t2[k];
    } else if (k>=TABLEN) {
      fac = 0.0;
    } else {
      fac = t1[k] + rSquared * t2[k];
    }

    potential += fac;
  }
    
  return potential;
}

void
calculateGradient(struct part *p, struct xyz *position, struct xyz *force)
{
  int j;
  int k;
  double rSquared;
  double fac;
  struct xyz v1;
  struct xyz v2;
  double z;
  double theta;
  double ff;

  /* interpolation */
  double *t1;
  double *t2;
  double start;
  int scale;

  struct interpolationTable *iTable;
  struct stretch *stretch;
  struct bond *bond;
  struct bond *bond1;
  struct bond *bond2;
  struct bend *bend;
  struct bendData *bType;
  double torque;
  struct vanDerWaals *vdw;
  struct xyz r;
  struct xyz q1;
  struct xyz q2;
  struct xyz foo;
  struct xyz f;

  validSerial++;
    
  /* clear force vectors */
  for (j=0; j<p->num_atoms; j++) {
    vsetc(force[j], 0.0);
  }

  for (j=0; j<p->num_stretches; j++) {
    stretch = &p->stretches[j];
    bond = stretch->b;

    // we presume here that rUnit is invalid, and we need r and
    // rSquared anyway.
    setRUnit(position, bond, &rSquared);

    // table lookup equivalent to: fac = gradientLippincottMorse(rSquared);
    iTable = &stretch->stretchType->gradientLippincottMorse;
    start = iTable->start;
    scale = iTable->scale;
    t1 = iTable->t1;
    t2 = iTable->t2;
    k = (int)(rSquared - start) / scale;
    if (k < 0) {
      if (!ToMinimize && DEBUG(D_TABLE_BOUNDS)) { //linear
        fprintf(stderr, "stretch: low --");
        printStretch(stderr, p, stretch);
      }
      fac = t1[0] + rSquared * t2[0];
    } else if (k >= TABLEN) {
      if (ToMinimize) { // quadratic potential past table gives linear gradient (in r, not r^2)
        fac = 2.0 * stretch->stretchType->potentialExtensionStiffness * sqrt(rSquared);
        //fac = t1[TABLEN-1]+ ((TABLEN-1) * scale + start) * t2[TABLEN-1];
      } else {
        fac=0.0;
        if (DEBUG(D_TABLE_BOUNDS)) {
          fprintf(stderr, "stretch: high --");
          printStretch(stderr, p, stretch);
        }
      }
    } else {
      fac = t1[k] + rSquared * t2[k];
    }
            
    vmul2c(f, bond->rUnit, fac);  // f = gradientLippincottMorse(rSquared)
    vadd(force[bond->a1->index], f);
    vsub(force[bond->a2->index], f);
  }
			
  /* now the forces for each bend */
			
  for (j=0; j<p->num_bends; j++) {
    bend = &p->bends[j];

    bond1 = bend->b1;
    bond2 = bend->b2;

    // Update rUnit for both bonds, if necessary.  Note that we
    // don't need r or rSquared here.
    if (bond1->valid != validSerial) {
      setRUnit(position, bond1, NULL);
    }
    if (bond2->valid != validSerial) {
      setRUnit(position, bond2, NULL);
    }
      
    // v1, v2 are the unit vectors FROM the central atom TO the
    // neighbors.  Reverse them if we have to.
    if (bend->dir1) {
      vsetn(v1, bond1->rUnit);
    } else {
      vset(v1, bond1->rUnit);
    }
    if (bend->dir2) {
      vsetn(v2, bond2->rUnit);
    } else {
      vset(v2, bond2->rUnit);
    }

    // XXX figure out how close we can get / need to get
    // apply no force if v1 and v2 are close to being linear
    if (-0.99 < vdot(v1,v2)) {

      z = vlen(vsum(v1, v2));
      // this is the equivalent of theta=arccos(z);
      theta = Pi + z * (ACOS_POLY_D +
                   z * (ACOS_POLY_C +
                   z * (ACOS_POLY_B +
                   z *  ACOS_POLY_A   )));

      v2x(foo, v1, v2);       // foo = v1 cross v2
      foo = uvec(foo);        // hmmm... not sure why this has to be a unit vector.
      q1 = uvec(vx(v1, foo)); // unit vector perpendicular to v1 in plane of v1 and v2
      q2 = uvec(vx(foo, v2)); // unit vector perpendicular to v2 in plane of v1 and v2

      bType = bend->bendType;
      torque = (theta - bType->theta0) * bType->kb;
      ff = torque * bond1->inverseLength;
      vmulc(q1, ff);
      ff = torque * bond2->inverseLength;
      vmulc(q2, ff);

      vadd(force[bend->ac->index], q1);
      vsub(force[bend->a1->index], q1);
      vadd(force[bend->ac->index], q2);
      vsub(force[bend->a2->index], q2);
    }
  }

  /* do the van der Waals/London forces */
  for (j=0; j<p->num_vanDerWaals; j++) {
    vdw = p->vanDerWaals[j];

    // The vanDerWaals array changes over time, and might have
    // NULL's in it as entries are deleted.
    if (vdw == NULL) {
      continue;
    }
      
    vsub2(r, position[vdw->a1->index], position[vdw->a2->index]);
    rSquared = vdot(r, r);
      
    /* table setup  */
    iTable = &vdw->parameters->gradientBuckingham;
    start = iTable->start;
    scale = iTable->scale;
    t1 = iTable->t1;
    t2 = iTable->t2;
					
    k=(int)(rSquared - start) / scale;
    if (k < 0) {
      if (!ToMinimize && DEBUG(D_TABLE_BOUNDS)) { //linear
        fprintf(stderr, "vdW: off table low -- r=%.2f \n",  sqrt(rSquared));
        printVanDerWaals(stderr, p, vdw);
      }
      k=0;
      fac = t1[k] + rSquared * t2[k];
    } else if (k>=TABLEN) {
      fac = 0.0;
    } else {
      fac = t1[k] + rSquared * t2[k];
    }
      
    vmul2c(f, r, fac);
    vadd(force[vdw->a1->index], f);
    vsub(force[vdw->a2->index], f);
  }
}
