"""Test generic functions"""

from unittest import TestCase, makeSuite, TestSuite

import operator, string
from types import ClassType, InstanceType

from protocols.dispatch import *
from protocols import Interface,advise,declareImplementation

class Vehicle(object):  pass
class LandVehicle(Vehicle): pass
class WaterVehicle(Vehicle): pass

class Wheeled(Interface):
    pass

class FourWheeled(Wheeled):
    pass

class TwoWheeled(Wheeled):
    pass

class GasPowered:
    pass

class HumanPowered:
    pass

class Bicycle(HumanPowered,LandVehicle): advise(instancesProvide=[TwoWheeled])
class Hummer(GasPowered,LandVehicle): advise(instancesProvide=[FourWheeled])
class Speedboat(GasPowered,WaterVehicle): pass
class PaddleBoat(HumanPowered,WaterVehicle): pass








class TermTests(TestCase):

    def testClassTermMembership(self):

        hp = ITerm(HumanPowered)

        self.failUnless(PaddleBoat in hp)
        self.failUnless(Bicycle in hp)

        self.failIf(Vehicle in hp)
        self.failIf(Speedboat in hp)
        self.failIf(Hummer in hp)
        self.failIf(object in hp)

        it = ITerm(InstanceType)
        ob = ITerm(object)

        for klass in (GasPowered,HumanPowered):
            self.failUnless(klass in it)
            self.failUnless(klass in ob)

        for klass in (Vehicle,LandVehicle,WaterVehicle,Bicycle,Hummer,
            Speedboat,PaddleBoat
        ):
            self.failIf(klass in it)
            self.failUnless(klass in ob)


    def testTermImplication(self):
        self.failUnless(ITerm(Bicycle).implies(Wheeled))
        self.failUnless(ITerm(PaddleBoat).implies(HumanPowered))
        self.failUnless(ITerm(Hummer).implies(FourWheeled))
        self.failUnless(ITerm(Hummer).implies(LandVehicle))
        self.failUnless(ITerm(Speedboat).implies(Vehicle))
        self.failUnless(ITerm(Wheeled).implies(object))
        self.failUnless(ITerm(GasPowered).implies(InstanceType))
        self.failUnless(ITerm(Wheeled).implies(Vehicle))
        self.failIf(ITerm(object).implies(Speedboat))



    def testNullTerm(self):
        # Null term has no seeds
        self.failIf(list(NullTerm.seeds()))

        # and it matches anything
        self.failUnless(object in NullTerm)
        self.failUnless(Speedboat in NullTerm)

        # is implied by everything
        self.failUnless(ITerm(Vehicle).implies(NullTerm))

        # and implies nothing
        self.failIf(NullTerm.implies(object))


    def testClassTermSeedsAndDispatchFunctions(self):
        for klass in (Vehicle,LandVehicle,WaterVehicle,HumanPowered,GasPowered):
            seeds = list(ITerm(klass).seeds())
            self.failUnless(klass in seeds)
            self.failUnless(object in seeds)
            self.failIf(len(seeds)<>2)
            self.failUnless(
                ITerm(klass).dispatch_function is dispatch_by_mro
            )

    def testTermAdaptation(self):
        self.failUnless(Hummer in ITerm(Wheeled))
        self.failIf(ITerm(Hummer).implies(Speedboat))
        self.failUnless(ITerm(Speedboat).implies(WaterVehicle))
        self.failUnless(object in list(ITerm(InstanceType).seeds()))

    def testProtocolTerm(self):
        self.failUnless(Bicycle in ITerm(Wheeled))
        seeds = list(ITerm(Wheeled).seeds())
        self.failUnless(Hummer in seeds)
        self.failUnless(Bicycle in seeds)
        self.failUnless(object in seeds)
        self.failUnless(len(seeds)==3)
        class BrokenBike(Bicycle): advise(instancesDoNotProvide=[Wheeled])
        self.failIf(BrokenBike in ITerm(Wheeled))

    def testSignatures(self):

        d1 = {0:ITerm(LandVehicle), 1:ITerm(WaterVehicle)}
        d2 = {0:ITerm(Hummer), 1:ITerm(Speedboat)}
        d3 = {0:ITerm(WaterVehicle), 1:ITerm(LandVehicle)}
        d4 = {0:ITerm(LandVehicle), 1:ITerm(LandVehicle)}

        for d in d1,d2,d3,d4:
            self.assertEqual( dict(Signature(d.items()).items()), d )

        s1 = Signature(d1.items())
        s2 = Signature(d2.items())
        s3 = Signature(d3.items())
        s4 = Signature(d4.items())
        s5 = PositionalSignature(
            (ITerm(LandVehicle),ITerm(WaterVehicle),ITerm(object))
        )

        self.failUnless(s2.implies(s1)); self.failIf(s1.implies(s2))
        self.failUnless(s5.implies(s1)); self.failIf(s1.implies(s3))

        self.failIf(s1.implies(s4)); self.failIf(s2.implies(s3))
        self.failIf(s2.implies(s4)); self.failIf(s1.implies(s5))

        all_sigs = [(s1,0),(s2,0),(s3,0),(s4,0),(s5,0)]

        self.assertEqual(
            most_specific_signatures(all_sigs), [(s2,0),(s3,0),(s4,0),(s5,0)]
        )

        self.assertEqual( most_specific_signatures([(s1,0),(s2,0)]), [(s2,0)] )

        self.assertEqual( ordered_signatures(all_sigs),
            [[(s2,0),(s3,0),(s4,0),(s5,0)],[(s1,0)]]
        )

        self.assertEqual( ordered_signatures([(s1,0),(s2,0)]),
            [[(s2,0)],[(s1,0)]]
        )


class GenericTest(TestCase):

    def testBasicSingleDispatch(self):
        m = PositionalGenericFunction()
        m[(LandVehicle,)] = lambda v: "land"
        m[(WaterVehicle,)] = lambda v: "water"

        self.assertEquals(m(Hummer()), "land")
        self.assertEquals(m(Speedboat()), "water")
        self.assertRaises(MessageNotUnderstood, m, GasPowered())


    def testSimpleDoubleDispatch(self):
        faster = PositionalGenericFunction()
        faster[(GasPowered,HumanPowered)] = lambda v1,v2: True
        faster[(Hummer,Speedboat)] = lambda v1,v2: True
        faster[(object,object)] = lambda v1,v2: "dunno"
        faster[(HumanPowered,GasPowered)] = lambda v1,v2: False
        faster[(Speedboat,Hummer)] = lambda v1,v2: False
        self.assertEqual(faster(Hummer(),Bicycle()), True)

    def testAmbiguity(self):
        add = PositionalGenericFunction()
        add[(object, int)] = operator.add
        add[(int, object)] = operator.sub
        self.assertRaises(AmbiguousMethod, add, 1, 2)

    def testDynamic(self):
        roll = PositionalGenericFunction()
        class Tricycle(HumanPowered,LandVehicle): pass
        roll[(Wheeled,)] = lambda ob: "We're rolling"
        self.assertRaises(MessageNotUnderstood, roll, Tricycle())
        declareImplementation(Tricycle,[Wheeled])
        self.assertEqual(roll(Tricycle()),"We're rolling")







    def testSimpleChaining(self):

        def both_vehicles(ob1,ob2):
            return "They're both vehicles."

        def both_land(ob1,ob2):
            return next_method(ob1,ob2)+"  They are both land vehicles."

        def both_sea(ob1,ob2):
            return next_method(ob1,ob2)+"  They are both sea vehicles."

        def mixed_vehicles(ob1,ob2):
            return next_method(ob1,ob2)+ \
                "  One vehicle is a land vehicle, the other is a sea vehicle."

        compare = PositionalGenericFunction(method_combiner = chained_methods)
        compare.addMethod([(Vehicle, Vehicle)], both_vehicles)
        compare.addMethod([(LandVehicle, LandVehicle)],both_land)
        compare.addMethod([(WaterVehicle, WaterVehicle)],both_sea)

        compare.addMethod(
            [(LandVehicle, WaterVehicle),(WaterVehicle, LandVehicle)],
            mixed_vehicles
        )

        land = Bicycle()
        sea = Speedboat()

        self.assertEqual( compare(land, land),
            "They're both vehicles.  They are both land vehicles.")

        self.assertEqual( compare(sea, sea),
            "They're both vehicles.  They are both sea vehicles.")

        self.assertEqual( compare(land, sea), "They're both vehicles.  \
One vehicle is a land vehicle, the other is a sea vehicle.")

        self.assertEqual( compare(sea, land), "They're both vehicles.  \
One vehicle is a land vehicle, the other is a sea vehicle.")


    def testSimpleMultiDispatch(self):
        class A: pass
        class B(A): pass
        class C: pass
        class D(A,C): pass

        def m1(*x): return "m1"
        def m2(*x): return "m2"
        def m3(*x): return "m3"
        def m4(*x): return "m4"
        def m5(*x): return "m5"

        class T: pass
        class F: pass

        tf = [F(),T()]

        g = PositionalGenericFunction()

        # f1, f1.x, f2, f1.x@!B, f1.y=f2.y

        g.addMethod([(A,A,NullTerm,T,T)], m1)
        g.addMethod([(B,B),(C,B,A)], m2)
        g.addMethod([(C,NullTerm,C)], m3)
        g.addMethod([(C,)], m4)
        g.addMethod([(T,)], m5)

        def w(f1,f1x,f2,ymatches=F()):
            return g(f1,f1x,f2,tf[not isinstance(f1x,B)],ymatches)

        self.assertEqual( w(A(),A(),C(),T()), "m1")
        self.assertEqual( w(B(),B(),C()),     "m2")
        self.assertEqual( w(C(),B(),B()),     "m2")
        self.assertEqual( w(C(),C(),C()),     "m3")
        self.assertEqual( w(C(),A(),A()),     "m4")
        self.assertEqual( g(T()),             "m5")





TestClasses = (
    TermTests, GenericTest,
)

def test_suite():
    s = []
    for t in TestClasses:
        s.append(makeSuite(t,'test'))

    return TestSuite(s)































