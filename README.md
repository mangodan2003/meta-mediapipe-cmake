# meta-mediapipe-cmake

## Overview

This is a somewhat hack attempt at trying to build mediapipe as a shared library with cmake.

We apply mediapipe patches to tflite and build that with cmake.

Then parse mediapipes bazel configration to produce a tree CMakeLists.txt and required source files

Finally we build it.


