"""Test generic functions"""

from unittest import TestCase, makeSuite, TestSuite

import operator, string
from types import ClassType, InstanceType

import dispatch,protocols
from dispatch import *
from dispatch.predicates import *
from protocols import Interface,advise,declareImplementation
from dispatch import strategy
from dispatch.strategy import most_specific_signatures, ordered_signatures

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
class RiverBoat(WaterVehicle):
    advise(instancesProvide=[TwoWheeled])


class TestTests(TestCase):

    def testClassTestMembership(self):

        hp = ITest(HumanPowered)

        self.failUnless(PaddleBoat in hp)
        self.failUnless(Bicycle in hp)

        self.failIf(Vehicle in hp)
        self.failIf(Speedboat in hp)
        self.failIf(Hummer in hp)
        self.failIf(object in hp)

        it = ITest(InstanceType)
        ob = ITest(object)

        for klass in (GasPowered,HumanPowered):
            self.failUnless(klass in it)
            self.failUnless(klass in ob)

        for klass in (Vehicle,LandVehicle,WaterVehicle,Bicycle,Hummer,
            Speedboat,PaddleBoat
        ):
            self.failIf(klass in it)
            self.failUnless(klass in ob)


    def testTestImplication(self):
        self.failUnless(ITest(Bicycle).implies(Wheeled))
        self.failUnless(ITest(PaddleBoat).implies(HumanPowered))
        self.failUnless(ITest(Hummer).implies(FourWheeled))
        self.failUnless(ITest(Hummer).implies(LandVehicle))
        self.failUnless(ITest(Speedboat).implies(Vehicle))
        self.failUnless(ITest(Wheeled).implies(object))
        self.failUnless(ITest(GasPowered).implies(InstanceType))
        self.failUnless(ITest(Wheeled).implies(Vehicle))
        self.failIf(ITest(object).implies(Speedboat))



    def testNullTest(self):
        # Null test has no seeds
        self.failIf(list(NullTest.seeds({})))

        # and it matches anything
        self.failUnless(object in NullTest)
        self.failUnless(Speedboat in NullTest)

        # is implied by everything
        self.failUnless(ITest(Vehicle).implies(NullTest))

        # and implies nothing
        self.failIf(NullTest.implies(object))


    def testClassTestSeedsAndDispatchFunctions(self):
        for klass in (Vehicle,LandVehicle,WaterVehicle,HumanPowered,GasPowered):
            seeds = list(ITest(klass).seeds({}))
            self.failUnless(klass in seeds)
            self.failUnless(object in seeds)
            self.failIf(len(seeds)<>2)
            self.failUnless(
                ITest(klass).dispatch_function is strategy.dispatch_by_mro
            )

    def testTestAdaptation(self):
        self.failUnless(Hummer in ITest(Wheeled))
        self.failIf(ITest(Hummer).implies(Speedboat))
        self.failUnless(ITest(Speedboat).implies(WaterVehicle))
        self.failUnless(object in list(ITest(InstanceType).seeds({})))

    def testProtocolTest(self):
        self.failUnless(Bicycle in ITest(Wheeled))
        seeds = list(ITest(Wheeled).seeds({}))
        self.failUnless(Hummer in seeds)
        self.failUnless(Bicycle in seeds)
        self.failUnless(object in seeds)
        self.failUnless(len(seeds)==4)
        class BrokenBike(Bicycle): advise(instancesDoNotProvide=[Wheeled])
        self.failIf(BrokenBike in ITest(Wheeled))

    def testSignatures(self):
        a0 = Argument(0); a1 = Argument(1)
        d1 = {a0:ITest(LandVehicle), a1:ITest(WaterVehicle)}
        d2 = {a0:ITest(Hummer), a1:ITest(Speedboat)}
        d3 = {a0:ITest(WaterVehicle), a1:ITest(LandVehicle)}
        d4 = {a0:ITest(LandVehicle), a1:ITest(LandVehicle)}

        for d in d1,d2,d3,d4:
            self.assertEqual( dict(Signature(d.items()).items()),
                dict([((k,v.dispatch_function),v) for k,v in d.items()]) )

        s1 = Signature(d1.items())
        s2 = Signature(d2.items())
        s3 = Signature(d3.items())
        s4 = Signature(d4.items())
        s5 = PositionalSignature(
            (ITest(LandVehicle),ITest(WaterVehicle),ITest(object))
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

    def testMinMax(self):
        self.failUnless(Min < Max)
        self.failUnless(Max > Min)
        self.failUnless(Max == Max)
        self.failUnless(Min == Min)
        self.failIf(Min==Max or Max==Min)
        self.failUnless(Max > "xyz")
        self.failUnless(Min < "xyz")
        self.failUnless(Max > 999999)
        self.failUnless(Min < -999999)
        data = [(27,Max),(Min,99),(53,Max),(Min,27),(53,56)]
        data.sort()
        self.assertEqual(data,
            [(Min,27),(Min,99),(27,Max),(53,56),(53,Max)]
        )


    def testInequalities(self):
        self.assertRaises(ValueError, Inequality, '', 1)
        self.assertRaises(ValueError, Inequality, 'xyz', 2)
        t1 = Inequality('>',55); t2 = Inequality('>=',100)

        self.failIf( (55,55) in t1 )
        self.failIf( (55,55) in t2 )

        self.failUnless( (100,100) in t2 )
        self.failUnless( (100,100) in t1 )
        self.failUnless( (101,101) in t2 )
        self.failUnless( (110,Max) in t2 )

        self.failUnless(t2.implies(t1))
        self.failIf(t1.implies(t2))

        t3 = Inequality('<',99)
        self.failIf(t1.implies(t3) or t2.implies(t3))
        self.failIf(t3.implies(t1) or t3.implies(t2))

        t4 = Inequality('<',"abc")
        self.failUnless(("a","a") in t4); self.failIf(("b","b") in t4)


    def testInequalitySeeds(self):
        t1 = Inequality('>',27); t2 = Inequality('<=',19)
        self.assertEqual(t1.seeds({}), [(Min,27),(27,27),(27,Max)])
        self.assertEqual(t2.seeds({}), [(Min,19),(19,19),(19,Max)])
        self.assertEqual(
            t1.seeds({(Min,19):[], (19,19):[], (19,Max):[]}),
            [(19,27),(27,27),(27,Max)]
        )
        self.assertEqual(
            t2.seeds({(Min,27):[], (27,27):[], (27,Max):[]}),
            [(Min,19),(19,19),(19,27)]
        )

        self.assertEqual(
            strategy.concatenate_ranges(
                {(Min,27):[], (27,27):[], (27,Max):[],
                 (Min,19):[], (19,19):[], (19,27): [],
                }
            ),
            [(Min,19),(19,27),(27,Max)],
        )
        self.assertEqual(
            strategy.concatenate_ranges(
                {(Min,19):[], (27,27):[], (19,Max):[],
                  (19,27):[], (19,19):[], (27,Max):[],
                }
            ),
            [(Min,19),(19,27),(27,Max)],
        )












    def testInequalityDispatch(self):
        classify = GenericFunction(args=['age'])
        classify[(Inequality('<',2),)]   = lambda age:"infant"
        classify[(Inequality('<',13),)]  = lambda age:"preteen"
        classify[(Inequality('<',5),)]   = lambda age:"preschooler"
        classify[(Inequality('<',20),)]  = lambda age:"teenager"
        classify[(Inequality('>=',20),)] = lambda age:"adult"
        classify[(Inequality('>=',55),)] = lambda age:"senior"
        classify[(Inequality('=',16),)]  = lambda age:"sweet sixteen"

        self.assertEqual(classify(25),"adult")
        self.assertEqual(classify(17),"teenager")
        self.assertEqual(classify(13),"teenager")
        self.assertEqual(classify(12.99),"preteen")
        self.assertEqual(classify(0),"infant")
        self.assertEqual(classify(4),"preschooler")
        self.assertEqual(classify(55),"senior")
        self.assertEqual(classify(54.9),"adult")
        self.assertEqual(classify(14.5),"teenager")
        self.assertEqual(classify(16),"sweet sixteen")
        self.assertEqual(classify(16.5),"teenager")
        self.assertEqual(classify(99),"senior")
        self.assertEqual(classify(Min),"infant")
        self.assertEqual(classify(Max),"senior")


    def testTruth(self):
        self.assertEqual(TruthTest(27), TruthTest("abc"))
        self.assertNotEqual(TruthTest(1), TruthTest(False))
        self.failUnless(True in TruthTest(1))
        self.failUnless(False not in TruthTest(1))
        self.failUnless(True not in TruthTest(0))
        self.failUnless(False in TruthTest(0))
        self.failIf(TruthTest(1).implies(TruthTest(0)))
        self.failIf(TruthTest(0).implies(TruthTest(1)))
        self.failUnless(TruthTest(0).implies(TruthTest(0)))
        self.failUnless(TruthTest(1).implies(TruthTest(1)))
        self.assertEqual(TruthTest(42).seeds({}), (True,False))
        self.assertEqual(TruthTest(None).seeds({}), (True,False))


    def testAndOr(self):
        def is_in(items):
            return OrTest(*[Inequality('==',x) for x in items])

        equals_two = Inequality('==',2)
        odd_primes = is_in([3,5,7,11,13,19])
        lo_primes = OrTest(equals_two, odd_primes)
        self.assertEqual(lo_primes.tests[1:], odd_primes.tests) # flattening
        self.failIf((4,4) in lo_primes)
        self.failUnless((11,11) in lo_primes)

        # Rephrase as And(Not(), Or(...)), so we can confirm other implications
        lo_primes = is_in([2,3,5,7,11,13,19])
        odd_primes = AndTest(NotTest(equals_two), lo_primes)
        self.failIf((4,4) in lo_primes)
        self.failUnless((11,11) in lo_primes)

        odd_nums  = is_in([1,3,5,7,9,11,13,15,19])
        even_nums = is_in([2,4,6,8,10,12,14])
        even_primes = AndTest(lo_primes,even_nums)

        self.failIf((3,3) in even_nums)
        self.failUnless((4,4) in even_nums)

        self.failIf((3,3) in even_primes)
        self.failUnless((2,2) in even_primes)

        self.failUnless(odd_primes.implies(odd_nums))
        self.failUnless(odd_primes.implies(lo_primes))
        self.failUnless(even_primes.implies(even_nums))

        self.failIf(lo_primes.implies(even_nums))
        self.failIf(odd_primes.implies(even_nums))

        self.failUnless(odd_primes.implies(NullTest))
        self.failUnless(even_primes.implies(NullTest))
        self.failUnless(lo_primes.implies(NullTest))
        self.assertRaises(ValueError, AndTest, Inequality('==',1), TruthTest(1))
        self.assertRaises(ValueError, OrTest, Inequality('==',1), HumanPowered)


    def testRangeIntersection(self):
        ten_to_twenty = AndTest(Inequality('>=',10), Inequality('<=',20))
        fifteen_to_nineteen = AndTest(Inequality('>=',15), Inequality('<=',19))

        self.failUnless( (5,5) not in ten_to_twenty )
        self.failUnless( (5,5) not in fifteen_to_nineteen )
        self.failUnless( (15,15) in ten_to_twenty )
        self.failUnless( (15,15) in fifteen_to_nineteen )
        self.failUnless( (10,10) in ten_to_twenty )
        self.failUnless( (16,17) in fifteen_to_nineteen)

        self.failUnless( fifteen_to_nineteen.implies(ten_to_twenty) )
        self.failIf(ten_to_twenty.implies(fifteen_to_nineteen))

        self.failUnless(
            NotTest(ten_to_twenty).implies(NotTest(fifteen_to_nineteen))
        )
        self.failIf(
            NotTest(fifteen_to_nineteen).implies(NotTest(ten_to_twenty))
        )

        either = OrTest(fifteen_to_nineteen,ten_to_twenty)
        for item in fifteen_to_nineteen, ten_to_twenty:
            self.failUnless( item.implies(either) )
            self.failUnless( item.implies(NullTest) )
            self.failUnless( NotTest(item).implies(NullTest) )


    def testClassIntersections(self):
        self.failUnless( Hummer in AndTest(LandVehicle,GasPowered) )
        self.failUnless( Speedboat in NotTest(LandVehicle) )
        self.failUnless( Bicycle in OrTest(NotTest(HumanPowered),LandVehicle) )
        self.failUnless( AndTest(LandVehicle,GasPowered).implies(GasPowered) )

        # This implication doesn't hold true because RiverBoat is a Wheeled
        # non-LandVehicle; if Riverboat didn't exist the implication would hold
        self.failIf( NotTest(LandVehicle).implies(NotTest(Wheeled)) )




    def testSimplifications(self):
        self.assertEqual(NotTest(TruthTest(1)), TruthTest(0))
        self.assertEqual(NotTest(NotTest(TruthTest(1))), TruthTest(27))

        self.assertEqual(
            NotTest(AndTest(Inequality('>=',10),Inequality('<=',20))),
            OrTest(NotTest(Inequality('>=',10)),NotTest(Inequality('<=',20)))
        )

        self.assertEqual(
            NotTest(OrTest(Inequality('>=',10),Inequality('<=',20))),
            AndTest(NotTest(Inequality('>=',10)),NotTest(Inequality('<=',20)))
        )

        self.assertEqual(
            AndTest(AndTest(Inequality('>=',10),Inequality('<=',20)),
                Inequality('==',15)
            ),
            AndTest(Inequality('>=',10),Inequality('<=',20),Inequality('==',15))
        )

        self.assertEqual(
            OrTest(OrTest(Inequality('>=',10),Inequality('<=',20)),
                Inequality('==',15)
            ),
            OrTest(Inequality('>=',10),Inequality('<=',20),Inequality('==',15))
        )


    def testTruthDispatch(self):
        x_gt_y = Call(operator.gt, Argument(name='x'), Argument(name='y'))
        greater = GenericFunction(args=['x','y'])
        greater[Signature([(x_gt_y, TruthTest(False))])] = lambda x,y: False
        greater[Signature([(x_gt_y, TruthTest(True))])]  = lambda x,y: True

        self.failIf(greater(1,10))
        self.failIf(greater(1,1))
        self.failUnless(greater(2,1))



    def testSignatureArithmetic(self):

        x_gt_10 = Signature(x=Inequality('>',10))
        x_lt_20 = Signature(x=Inequality('<',20))
        y_in_LandVehicle = Signature(y=LandVehicle)
        empty = Signature()

        self.assertEqual((x_gt_10 & x_lt_20),
            Signature(x=AndTest(Inequality('>',10),Inequality('<',20)))
        )

        self.assertEqual((x_gt_10 & y_in_LandVehicle),
            Signature(x=Inequality('>',10),y=LandVehicle)
        )

        self.assertEqual((x_gt_10 & x_gt_10), x_gt_10)
        self.assertEqual((x_gt_10 & empty), x_gt_10)
        self.assertEqual((empty & x_gt_10), x_gt_10)

        self.assertEqual((x_gt_10 | empty), empty)
        self.assertEqual((empty | x_gt_10), empty)
        self.assertEqual((x_gt_10 | x_lt_20),
            Signature(x=OrTest(Inequality('>',10),Inequality('<',20)))
        )
        self.assertEqual((x_gt_10 | y_in_LandVehicle),
            Predicate([x_gt_10,y_in_LandVehicle])
        )

        # sig | pred
        self.assertEqual((x_gt_10 | Predicate([y_in_LandVehicle])),
            Predicate([x_gt_10,y_in_LandVehicle])
        )
        # sig & pred
        self.assertEqual((x_gt_10 & Predicate([y_in_LandVehicle])),
            Predicate([x_gt_10 & y_in_LandVehicle])
        )





        # pred | pred
        self.assertEqual((Predicate([x_gt_10]) | Predicate([y_in_LandVehicle])),
            Predicate([x_gt_10, y_in_LandVehicle])
        )

        # pred & pred
        self.assertEqual((Predicate([x_gt_10]) & Predicate([y_in_LandVehicle])),
            Predicate([x_gt_10 & y_in_LandVehicle])
        )
































class ExpressionTests(TestCase):

    def testArgumentBasics(self):

        self.assertRaises(ValueError, Argument)     # must specify name or posn

        self.failUnless(Argument(0) == Argument(0))
        self.failIf(    Argument(0) == Argument(1))

        self.failUnless(Argument(name="x") == Argument(name="x"))
        self.failIf(    Argument(name="x") == Argument(name="y"))

        self.failIf(    Argument(name="x") == Argument(1,"x"))
        self.failIf(    Argument(1,"x")    == Argument(name="x"))
        self.failIf(    Argument(1)        == Argument(1,"x"))
        self.failIf(    Argument(1,"x")    == Argument(1))

        self.failUnless(Argument(0,"x")    == Argument(0,"x"))
        self.failIf(    Argument(0,"x")    == Argument(0,"y"))
        self.failIf(    Argument(0,"x")    == Argument(1,"x"))
        self.failIf(    Argument(0,"x")    == Argument(1,"y"))

        a1 = Argument(0,"x"); a2 = Argument(0,"x")
        self.assertEqual(hash(a1), hash(a2))

        a1 = Argument(1); a2 = Argument(1)
        self.assertEqual(hash(a1), hash(a2))

        a1 = Argument(name="x"); a2 = Argument(name="x")
        self.assertEqual(hash(a1), hash(a2))











    def testFunctionArguments(self):

        f = GenericFunction(args=['a','b','c'])

        fa,arga = f.argByName('a')
        fb,argb = f.argByName('b')
        fc,argc = f.argByName('c')

        self.assertEqual(f.argByName('a'), f.argByName('a'))

        for arg in arga,argb,argc:
            self.assertEqual(arg, (RAW_VARARGS_ID,RAW_KWDARGS_ID))

        args = (1,2,3); kw={'a':1, 'b':2, 'c':3}

        self.assertEqual(fa(args,{}), 1)
        self.assertEqual(fb(args,{}), 2)
        self.assertEqual(fc(args,{}), 3)

        self.assertEqual(fa((),kw), 1)
        self.assertEqual(fb((),kw), 2)
        self.assertEqual(fc((),kw), 3)

        self.assertRaises(KeyError, f.argByName, 'x')


    def testArgumentCanonicalization(self):
        f = GenericFunction(args=['v1','v2'])
        self.assertEqual(
            f.getExpressionId(Argument(name='v1')),
            f.getExpressionId(Argument(0))
        )
        self.assertEqual(
            f.getExpressionId(Argument(name='v2')),
            f.getExpressionId(Argument(1))
        )





    def testCalls(self):
        self.assertEqual(Call(operator.add,1,2), Call(operator.add,1,2))
        self.assertNotEqual(Call(operator.sub,1,2), Call(operator.add,1,2))
        self.assertNotEqual(Call(operator.add,2,1), Call(operator.add,1,2))

        c1 = Call(operator.add, Argument(name='x'), Argument(name='y'))
        c2 = Call(operator.add, Argument(name='x'), Argument(name='y'))
        self.assertEqual(hash(c1), hash(c2))

        c3 = Call(operator.sub, Argument(name='x'), Argument(name='y'))
        self.assertNotEqual(hash(c1), hash(c3))

        f = GenericFunction(args=['x','y'])
        self.assertEqual(f.getExpressionId(c1), f.getExpressionId(c2))
        self.assertNotEqual(f.getExpressionId(c1), f.getExpressionId(c3))
        self.assertEqual(
            f.getExpressionId(c3),
            f.getExpressionId(
                Call(operator.sub, Argument(name='x'), Argument(name='y'))
            )
        )

        # Make the function handle 'x+y > 100'
        f[Signature([(c1,Inequality('>',100))])] = lambda x,y: "yes"
        f[Signature([])] = lambda x,y: "no"

        self.assertEqual(f(51,49), "no")
        self.assertEqual(f(99,10), "yes")
        self.assertEqual(f(27,89), "yes")












    def testConsts(self):
        f = GenericFunction(args=['x'])
        x_plus_two = Call(operator.add,Argument(name='x'),Const(2))

        f[Signature([(x_plus_two,Inequality('>',10))])] = lambda x: True
        f[Signature([])] = lambda x: False

        self.failUnless(f(9))
        self.failIf(f(8))

        foo, bar, fourA, fourB = Const("foo"),Const("bar"),Const(4),Const(4)
        self.assertEqual(fourA,fourB)
        self.assertEqual(hash(fourA),hash(fourB))
        self.assertNotEqual(bar,foo)
        self.assertNotEqual(hash(bar),hash(foo))


    def testGetattr(self):
        vehicle_mpg = Getattr(Argument(name='v'),'mpg')
        test_mpg = lambda test,val: (vehicle_mpg,Inequality(test,val))
        fuel_efficient = GenericFunction(args=['v'])
        fuel_efficient[Signature([test_mpg('==','N/A')])] = lambda v: True
        fuel_efficient[Signature([test_mpg('>',35)])]     = lambda v: True
        fuel_efficient[Signature([])] = lambda v: False

        b=Bicycle(); b.mpg = 'N/A'; h=Hummer();  h.mpg = 10
        self.failUnless(fuel_efficient(b))
        self.failIf(fuel_efficient(h))

        vm2 = Getattr(Argument(name='v'),'mpg')
        xm = Getattr(Argument(name='x'),'mpg')
        vg = Getattr(Argument(name='v'),'gpm')

        self.assertEqual(vehicle_mpg, vm2)
        self.assertEqual(hash(vehicle_mpg), hash(vm2))
        for item in xm,vg:
            self.assertNotEqual(vehicle_mpg, item)
            self.assertNotEqual(hash(vehicle_mpg), hash(item))



    def testTuple(self):
        xy = Tuple(tuple,Argument(name='x'),Argument(name='y'))
        xy_is_one_two = GenericFunction(args=['x','y'])
        xy_is_one_two[Signature([(xy,Inequality('==',(1,2)))])] = lambda x,y:True
        xy_is_one_two[Signature([])] = lambda x,y: False

        self.failUnless(xy_is_one_two(1,2))
        self.failIf(xy_is_one_two(1,3))
        self.failIf(xy_is_one_two(2,1))

        xy2 = Tuple(tuple,Argument(name='x'),Argument(name='y'))
        yx = Tuple(tuple,Argument(name='y'),Argument(name='x'))
        lx = Tuple(list,Argument(name='x'),Argument(name='y'))
        zz = Tuple(tuple,Argument(name='z'),Argument(name='z'))

        self.assertEqual(xy, xy2)
        self.assertEqual(hash(xy), hash(xy2))
        for item in yx,lx,zz:
            self.assertNotEqual(xy, item)
            self.assertNotEqual(hash(xy), hash(item))

    def testVar(self):
        d1={}; d2={}
        x = Var('x',d1,d2)
        foo = GenericFunction(args=[])
        foo[Signature([(x,Inequality('==',"foo"))])] = lambda: True
        foo[Signature([])] = lambda: False

        d2['x']="foo"; self.failUnless(foo())
        d1['x']="bar"; self.failIf(foo())
        del d2['x'];   self.failIf(foo())
        del d1['x'];   self.assertRaises(NameError, foo)

        x2 = Var('x',d1,d2)
        self.assertEqual(x, x2)
        self.assertEqual(hash(x), hash(x2))
        for item in Var('y',d1,d2),Var('x',d1),Var('x',d1,{}),Var('x',d2,d1):
            self.assertNotEqual(x, item)
            self.assertNotEqual(hash(x), hash(item))


    def testOrExpr(self):
        x, y = Argument(name='x'), Argument(name='y')
        z = Call(operator.div,Argument(name='y'),Argument(name='z'))

        xyz = OrExpr(x,y,z)
        or_ = GenericFunction(args=['x','y','z'])
        or_[Signature([(xyz,TruthTest())])] = lambda x,y,z:True
        or_[Signature([])] = lambda x,y,z: False

        self.failUnless(or_(1,0,1))
        self.failIf(or_(0,0,1))
        self.assertRaises(ZeroDivisionError,or_,0,0,0)

        zyx = OrExpr(z,y,x)
        xyz2 = OrExpr(x,y,z)
        xy  = OrExpr(x,y)

        self.assertEqual(xyz, xyz2)
        self.assertEqual(hash(xyz), hash(xyz2))
        for item in xy,zyx:
            self.assertNotEqual(xyz, item)
            self.assertNotEqual(hash(xyz), hash(item))

        or_eq_23 = GenericFunction(args=['x','y'])
        or_eq_23[Signature([(xy,Inequality('==',23))])] = lambda x,y:True
        or_eq_23[Signature([])] = lambda x,y: False
        self.failUnless(or_eq_23(23,0))
        self.failUnless(or_eq_23(0,23))
        self.failIf(or_eq_23(0,0))
        self.failIf(or_eq_23(15,15))

        or_eq_None = GenericFunction(args=['x','y'])
        or_eq_None[Signature([(xy,Inequality('==',None))])] = lambda x,y:True
        or_eq_None[Signature([])] = lambda x,y: False
        self.failUnless(or_eq_None(None,None))
        self.failUnless(or_eq_None(0,None))
        self.failIf(or_eq_None(1,None))
        self.failIf(or_eq_None(None,1))



    def testAndExpr(self):
        x, y = Argument(name='x'), Argument(name='y')
        z = Call(operator.div,Argument(name='y'),Argument(name='z'))

        xyz = AndExpr(x,y,z)
        and_ = GenericFunction(args=['x','y','z'])
        and_[Signature([(xyz,TruthTest())])] = lambda x,y,z:True
        and_[Signature([])] = lambda x,y,z: False

        self.failUnless(and_(True,True,True))
        self.failIf(and_(False,True,True))
        self.failIf(and_(False,27,0))
        self.assertRaises(ZeroDivisionError,and_,15,27,0)

        zyx = AndExpr(z,y,x)
        xyz2 = AndExpr(x,y,z)
        xy  = AndExpr(x,y)

        self.assertEqual(xyz, xyz2)
        self.assertEqual(hash(xyz), hash(xyz2))
        for item in xy,zyx:
            self.assertNotEqual(xyz, item)
            self.assertNotEqual(hash(xyz), hash(item))

        and_eq_23 = GenericFunction(args=['x','y'])
        and_eq_23[Signature([(xy,Inequality('==',23))])] = lambda x,y:True
        and_eq_23[Signature([])] = lambda x,y: False
        self.failUnless(and_eq_23(3,23))
        self.failUnless(and_eq_23(23,23))
        self.failIf(and_eq_23(23,15))
        self.failIf(and_eq_23(23,0))

        and_eq_None = GenericFunction(args=['x','y'])
        and_eq_None[Signature([(xy,Inequality('==',None))])] = lambda x,y:True
        and_eq_None[Signature([])] = lambda x,y: False
        self.failUnless(and_eq_None(None,None))
        self.failUnless(and_eq_None(1,None))
        self.failIf(and_eq_None(0,1))
        self.failIf(and_eq_None(1,0))


class SimpleGenerics(TestCase):

    def testTrivialities(self):
        for doc in "foo bar", "baz spam":
            g = dispatch.SimpleGeneric(doc)
            self.assertEqual(g.__doc__, doc)

            # Empty generic should raise NoApplicableMethods
            self.assertRaises(dispatch.NoApplicableMethods, g, 1, 2, 3)
            self.assertRaises(dispatch.NoApplicableMethods, g, "x", y="z")

            # Must have at least one argument to do dispatching
            self.assertRaises(TypeError, g)
            self.assertRaises(TypeError, g, foo="bar")

    def testSimpleDefinitions(self):
        g = dispatch.SimpleGeneric("x")

        class Classic: pass
        class NewStyle(object): pass
        class IFoo(protocols.Interface): pass
        class Impl: protocols.advise(instancesProvide=[IFoo])

        c=Classic()
        n=NewStyle()
        i=Impl()

        for item in c,n,i,1,"blue",SimpleGeneric:
            self.assertRaises(dispatch.NoApplicableMethods, g, item)

        dispatch.defmethod(g,Classic,lambda *args,**kw: ("classic!",args,kw))
        dispatch.defmethod(g,NewStyle,lambda *args,**kw: ("new!",args,kw))
        dispatch.defmethod(g,IFoo,lambda *args,**kw: ("foo!",args,kw))

        self.assertEqual(g(c,"foo"), ("classic!",(c,"foo",),{}))
        self.assertEqual(g(n,foo="bar"), ("new!",(n,),{'foo':'bar'}))
        self.assertEqual(g(i,"foo",x="y"), ("foo!",(i,"foo",),{"x":"y"}))

        for item in 1,"blue",SimpleGeneric:
            self.assertRaises(dispatch.NoApplicableMethods, g, item)

    def testMultiDefinition(self):

        class Classic: pass
        class NewStyle(object): pass
        class IFoo(protocols.Interface): pass
        class Impl: protocols.advise(instancesProvide=[IFoo])

        c=Classic()
        n=NewStyle()
        i=Impl()

        g = dispatch.SimpleGeneric("x")

        [dispatch.when([Classic,NewStyle,IFoo])]
        def g(*args,**kw):
            return ("yes!",args,kw)

        self.assertEqual(g(c,"foo"), ("yes!",(c,"foo",),{}))
        self.assertEqual(g(n,foo="bar"), ("yes!",(n,),{'foo':'bar'}))
        self.assertEqual(g(i,"foo",x="y"), ("yes!",(i,"foo",),{"x":"y"}))

        for item in 1,"blue",SimpleGeneric:
            self.assertRaises(dispatch.NoApplicableMethods, g, item)
        

    def testAdaptedDefinition(self):
        class Classic: pass
        g = dispatch.SimpleGeneric("x")

        [dispatch.when(dispatch.ISimpleDispatchPredicate)]
        def g(thing, *args,**kw):
            return thing

        it = g([Classic])
        self.assertNotEqual(it, [Classic])
        self.failUnless(dispatch.ISimpleDispatchPredicate(it) is it)





class GenericTests(TestCase):

    def testBasicSingleDispatch(self):
        m = GenericFunction(args=['v'])
        m[(LandVehicle,)] = lambda v: "land"
        m[(WaterVehicle,)] = lambda v: "water"
        self.assertEquals(m(Hummer()), "land")
        self.assertEquals(m(Speedboat()), "water")
        self.assertRaises(NoApplicableMethods, m, GasPowered())


    def testSimpleDoubleDispatchAndNamedArgs(self):
        faster = GenericFunction(args=['v1','v2'])
        faster[Signature(v1=GasPowered,v2=HumanPowered)] = lambda v1,v2: True
        faster[Signature(v1=Hummer,v2=Speedboat)] = lambda v1,v2: True
        faster[(object,object)] = lambda v1,v2: "dunno"
        faster[Signature(v1=HumanPowered,v2=GasPowered)] = lambda v1,v2: False
        faster[Signature(v2=Hummer,v1=Speedboat)] = lambda v1,v2: False
        self.assertEqual(faster(Hummer(),Bicycle()), True)

    def testAmbiguity(self):
        add = GenericFunction(args=['addend','augend'])
        add[(object, int)] = operator.add
        add[(int, object)] = operator.sub
        self.assertRaises(AmbiguousMethod, add, 1, 2)

    def testDynamic(self):
        roll = GenericFunction(args=['vehicle'])
        class Tricycle(HumanPowered,LandVehicle): pass
        roll[Signature(vehicle=Wheeled)] = lambda ob: "We're rolling"
        self.assertRaises(NoApplicableMethods, roll, Tricycle())
        declareImplementation(Tricycle,[Wheeled])
        self.assertEqual(roll(Tricycle()),"We're rolling")

    def testMRO(self):
        t = GenericFunction(args=['vehicle','num'])
        t[Signature(vehicle=HumanPowered,num=Inequality('<',10))]=lambda v,n:False
        t[Signature(vehicle=WaterVehicle,num=Inequality('<',5))]=lambda v,n:True
        self.assertRaises(AmbiguousMethod, t, PaddleBoat(), 4)


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

        compare = GenericFunction(args=['v1','v2'], method_combiner = chained_methods)
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

        g = GenericFunction(args=['f1','f1.x','f2','f1x@!B', 'f1.y==f2.y'])

        # f1, f1.x, f2, f1.x@!B, f1.y=f2.y

        g.addMethod([(A,A,NullTest,T,T)], m1)
        g.addMethod([(B,B),(C,B,A)], m2)
        g.addMethod([(C,NullTest,C)], m3)
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
    TestTests, ExpressionTests, SimpleGenerics, GenericTests,
)

def test_suite():
    s = []
    for t in TestClasses:
        s.append(makeSuite(t,'test'))

    return TestSuite(s)































