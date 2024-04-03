# -*- coding: utf-8 -*-
import context
import sys
import os

print("Context! " + os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import library
