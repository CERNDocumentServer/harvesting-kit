# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2014 CERN.
##
## Harvesting Kit is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Harvesting Kit is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from aps_package_tests import APSPackageTests
from elsevier_package_tests import ElsevierPackageTests
from edpsciencespackage_tests import EDPSciencesPackageTests
from pos_package_tests import POSPackageTests
import unittest


if __name__ == '__main__':
    suite1 = unittest.TestLoader().loadTestsFromTestCase(APSPackageTests)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(ElsevierPackageTests)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(EDPSciencesPackageTests)
    suite4 = unittest.TestLoader().loadTestsFromTestCase(POSPackageTests)
    alltests = unittest.TestSuite([suite1, suite2, suite3, suite4])
    unittest.TextTestRunner(verbosity=2).run(alltests)
