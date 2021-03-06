import itertools
import sys
import unittest

from justthisonce.interval import Interval

def _union_multi(ivals):
  """Unions all args pairwise left-associative."""
  if len(ivals) == 0:
    return Interval()
  else:
    acc = ivals[0]
    for ival in ivals[1:]:
      acc = acc.union(ival)
    return acc

class test_Interval(unittest.TestCase):
  def test_union_empty(self):
    """Test that empty intervals are well behaved."""
    a = Interval()
    b = Interval()
    c = a.union(b)
    d = b.union(a)
    self.assertEqual(a, b)
    self.assertEqual(b, c)
    self.assertEqual(c, d)

  def test_union_sym_comm(self):
    """Test that union is symmetric and commutative."""

    ivals = [Interval(), Interval.fromAtom(4, 2), Interval.fromAtom(6, 3), \
             Interval.fromAtom(11, 2), Interval.fromAtom(13, 15)]
    # If this were much larger we could use a prefix generator but I prefer
    # simplicity to speed in tests.
    correct = _union_multi(ivals)
    for iv in itertools.permutations(ivals):
      self.assertEqual(correct, _union_multi(iv))

  def test_union_merge_start_zero(self):
    """Tests merges for several coumpound intervals, all start at 0."""
    # Simple case with an extra hole in the original spec.
    a = Interval.fromAtoms([(0, 2), (4, 2), (6, 2)])
    b = Interval.fromAtoms([(2, 2)])
    self.assertEqual(a.union(b), Interval.fromAtom(0, 8))

    # Holes filled partially
    a = Interval.fromAtoms([(0, 2), (4, 2), (8, 2), (20, 3)])
    b = Interval.fromAtoms([(2, 1), (6, 1), (10, 5), (16, 4)])
    a_b = a.union(b)
    self.assertEqual(Interval.fromAtoms([(0, 3), (4, 3), (8, 7), (16, 7)]), a_b)
    a_b_c = a_b.union(Interval.fromAtoms([(3, 1), (7, 1)]))
    self.assertEqual(Interval.fromAtoms([(0, 15), (16, 7)]), a_b_c)
    a_b_c_d = a_b_c.union(Interval.fromAtom(15, 1))
    self.assertEqual(Interval.fromAtom(0, 23), a_b_c_d)
    self.assertEqual(len(a_b_c_d), 23)

  def test_union_merge_start_nonzero(self):
    """Tests merges for several coumpound intervals, all starting after 0
       (regression test against special-case bug)"""
    a = Interval.fromAtoms([(1, 2), (5, 2), (9, 2)])
    b = Interval.fromAtoms([(3, 2), (7, 1)])
    a_b = a.union(b)
    self.assertEqual(a_b, Interval.fromAtoms([(1, 7), (9, 2)]))
    a_b_c = Interval.fromAtom(8, 1).union(a_b)
    self.assertEqual(a_b_c, Interval.fromAtom(1, 10))
    self.assertEqual(len(a_b_c), 10)

  def test_eq_neq(self):
    """Makes sure equality and inequality work, since all other tests depend on
       them. I test many values because Python's default eq/neq behavion can
       be weird and miss edge cases."""
    # The other tests thoroughly test eq == true, so I focus on eq == false and
    # both values of ne.
    a = Interval.fromAtoms([(0, 2), (4, 2), (8, 2)])
    empty = Interval()
    self.assertFalse(a == Interval.fromAtoms([(0, 2)]))
    self.assertTrue(a != Interval.fromAtoms([(0, 2)]))

    self.assertTrue(a == a)
    self.assertFalse(a != a)

    self.assertFalse(a == empty)
    self.assertTrue(a != empty)

    self.assertTrue(empty == Interval())
    self.assertFalse(empty != Interval())

    self.assertTrue(empty == empty)
    self.assertFalse(empty != empty)

    b = Interval.fromAtoms([(0, 2), (4, 2), (6, 2)])
    c = Interval.fromAtoms([(0, 2), (4, 4)])
    self.assertTrue(b == c)
    self.assertFalse(b != c)

    self.assertFalse(b != b)
    self.assertTrue(b == b)
    self.assertFalse(c != c)
    self.assertTrue(c == Interval.fromAtoms([(0, 2), (4, 4)]))

  def test_constructor(self):
    """Tests that fromAtom can create empty intervals."""
    a = Interval.fromAtom(0, 0)
    b = Interval.fromAtom(10, 0)
    self.assertEqual(a, b)
    self.assertEqual(a, Interval())
    self.assertEqual(a, Interval.fromAtoms([(0, 0), (5, 0)]))

  def test_constructor_equiv(self):
    """Make sure the from* constructors are equivalent. (Default is tested
       with union)."""
    a = Interval.fromAtom(3, 4).union(Interval.fromAtom(12, 10))
    b = Interval.fromAtoms([(3, 4), (12, 10)])
    self.assertEqual(a, b)

    c = Interval.fromAtom(3, 4).union(Interval.fromAtom(7, 10))
    d = Interval.fromAtoms([(7, 10), (3, 4)])
    e = Interval.fromAtom(3, 14)
    self.assertEqual(c, d)
    self.assertEqual(d, e)

    # fromAtoms must tolerate 0-length intervals.
    f = Interval.fromAtoms([(0, 2), (2, 0), (2, 2)])
    self.assertEqual(f, Interval.fromAtom(0, 4))

    # and must not tolerate overlap.
    with self.assertRaises(AssertionError):
      Interval.fromAtoms([(0, 5), (4, 5)])

    # and should be able to create empty intervals (regression test)
    self.assertEqual(Interval.fromAtoms([]), Interval())
    self.assertEqual(Interval.fromAtoms([(5, 0)]), Interval())

  def test_len(self):
    """Specifically test len. This is also being tested in the object invariant
       throughout the entire test suite so we just do a quick one here."""
    a = Interval.fromAtom(3, 3)
    b = Interval.fromAtom(9, 5)
    self.assertEqual(len(a) + len(b), len(a.union(b)))
    self.assertEqual(len(a), 3)
    self.assertEqual(len(b), 5)
    self.assertEqual(len(Interval()), 0)

  def test_union_overlap(self):
    """It is part of the design spec that intervals to union must be disjoint,
       since otherwise would likely indicate an error in the main program."""
    # Off by one
    with self.assertRaises(AssertionError):
      Interval.fromAtom(0, 5).union(Interval.fromAtom(4, 5))
    a = Interval.fromAtom(0, 5).union(Interval.fromAtom(5, 5))
    self.assertEqual(a, Interval.fromAtom(0, 10))

    # Containment
    with self.assertRaises(AssertionError):
      Interval.fromAtom(0, 5).union(Interval.fromAtom(2, 1))
    with self.assertRaises(AssertionError):
      Interval.fromAtom(2, 1).union(Interval.fromAtom(0, 5))

    # Overlap by 1 (regression test)
    with self.assertRaises(AssertionError):
      Interval.fromAtom(0, 5).union(Interval.fromAtom(4, 1))
    
    # Multiple intervals
    b = Interval.fromAtoms([(2, 3), (10, 3), (20, 10000)])
    with self.assertRaises(AssertionError):
      Interval.fromAtom(0, 5).union(b)
    with self.assertRaises(AssertionError):
      Interval.fromAtom(2, 19).union(b)
    with self.assertRaises(AssertionError):
      Interval.fromAtom(900, 2).union(b)

    # With self
    with self.assertRaises(AssertionError):
      a.union(a)
    with self.assertRaises(AssertionError):
      b.union(b)

  def test_iterInterior(self):
    """Tests the iterInterior method."""
    atoms = [(0, 2), (4, 2), (8, 2)]
    self.assertEqual(atoms, list(Interval.fromAtoms(atoms).iterInterior()))
    self.assertEqual([], list(Interval().iterInterior()))

  def test_iterExterior(self):
    """Tests the iterExterior method."""
    atoms = [(0, 2), (4, 2), (8, 2)]
    ival = Interval.fromAtoms(atoms)
    self.assertEquals(list(ival.iterExterior()), [(2, 2), (6, 2)])
    self.assertEquals(list(ival.iterExterior(10)), [(2, 2), (6, 2)])
    self.assertRaises(AssertionError, lambda: list(ival.iterExterior(9)))
    self.assertEquals(list(ival.iterExterior(11)), [(2, 2), (6, 2), (10, 1)])
    self.assertEquals(list(ival.iterExterior(3000)), [(2, 2), (6, 2), (10, 2990)])

    # Length identities
    cmpl = Interval.fromAtoms(ival.iterExterior(50))
    self.assertEquals(len(cmpl) + len(ival), 50)
    self.assertEquals(cmpl.union(ival), Interval.fromAtom(0, 50))
    empty = Interval()
    for length in (0, 1, 2, 5):
      self.assertEquals(len(Interval.fromAtoms(empty.iterExterior(length))), \
                        length)
    ival = Interval.fromAtom(0, 1)
    for length in (1, 2, 5):
      self.assertEquals(len(Interval.fromAtoms(ival.iterExterior(length))), \
                        length - 1)

  def test_negative(self):
    """Ensures intervals reject negative lengths and/or spans."""
    # Negative start
    atoms = [(-2, 2), (2, 2), (8, 2)]
    self.assertRaises(AssertionError, Interval.fromAtoms, atoms)
    self.assertRaises(AssertionError, Interval.fromAtom, -1, 1)

    # Negative length
    atoms = [(0, 2), (2, -2), (8, 2)]
    self.assertRaises(AssertionError, Interval.fromAtoms, atoms)
    self.assertRaises(AssertionError, Interval.fromAtom, 1, -1)

  def test_min_max(self):
    """Test the min and max of the interval."""
    atoms = [(0, 2), (8, 2), (4, 2)]
    ival = Interval.fromAtoms(atoms)
    self.assertEquals(ival.min(), 0)
    self.assertEquals(ival.max(), 9)
    
    ival = Interval.fromAtom(5, 1)
    self.assertEquals(ival.min(), 5)
    self.assertEquals(ival.max(), 5)

    ival = Interval()
    self.assertIsNone(ival.min())
    self.assertIsNone(ival.max())

  def test_union_overlap(self):
    """Test that union works correctly when overlap is enabled."""
    a = Interval.fromAtom(5, 10)
    b = Interval.fromAtom(10, 10)
    self.assertEqual(a.union(b, allow_overlap=True), Interval.fromAtom(5, 15))

    a = Interval.fromAtom(5, 5)
    b = Interval.fromAtom(5, 15)
    self.assertEqual(a.union(b, allow_overlap=True), Interval.fromAtom(5, 15))

    a = Interval.fromAtom(5, 20)
    b = Interval.fromAtom(10, 15)
    self.assertEqual(a.union(b, allow_overlap=True), Interval.fromAtom(5, 20))

    a = Interval.fromAtom(10, 5)
    b = Interval.fromAtom(5, 15)
    self.assertEqual(a.union(b, allow_overlap=True), Interval.fromAtom(5, 15))

  def test_union_overlap_symmetry(self):
    """Test that the order does not matter."""

    for (a, b) in [(Interval.fromAtom(5, 10), Interval.fromAtom(10, 10)),
                   (Interval.fromAtom(5, 5), Interval.fromAtom(5, 15)),
                   (Interval.fromAtom(5, 20), Interval.fromAtom(10, 15)),
                   (Interval.fromAtom(10, 5), Interval.fromAtom(5, 15))]:
      self.assertEqual(a.union(b, allow_overlap=True), 
                       b.union(a, allow_overlap=True))

  def test_union_overlap_compound(self):
    """Test some compound cases of union with overlap."""
    a = Interval.fromAtoms([(5, 10), (20, 10), (50, 50)])
    b = Interval.fromAtoms([(0, 8), (10, 15), (28, 82)])
    self.assertEqual(a.union(b, True), b.union(a, True))
    self.assertEqual(a.union(b, True), Interval.fromAtom(0, 110))

    b = Interval.fromAtoms([(0, 8), (28, 82)])
    self.assertEqual(a.union(b, True), Interval.fromAtoms([(0, 15), (20, 90)]))

if __name__ == '__main__':
  unittest.main()
