DESCRIPTION = "Mediapipe C++ Library"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=87a30e5cfa12d1ab9ada4fb6f3feed4b"

DEPENDS = " \
    util-linux \
    bazel-native \
    protobuf-native \
    util-linux-native \
    protobuf \
    flatbuffers \
    opencv \
    python3 \
    python3-numpy-native \
    python3-keras-applications-native \
    python3-keras-preprocessing-native \
    python3-pip-native \
    python3-wheel-native \
    xxd-native \
    libusb1 \
    abseil-cpp \
    libeigen \
    tensorflow-lite \
    mesa \
    opencl-headers \
"
# Copied from opencv_linux.BUILD
RDEPENDS:${PN} = " \
    libopencv-core \
    libopencv-calib3d \
    libopencv-features2d \
    libopencv-highgui \
    libopencv-imgcodecs \
    libopencv-imgproc \
    libopencv-video \
    libopencv-videoio \
"

PACKAGECONFIG ?= "${@bb.utils.filter('DISTRO_FEATURES', 'opengl', d)}"
PACKAGECONFIG[opengl] = ",,mesa"

SRCREV = "37adc43cb9c70f9ed62e07c51b6ad2c04b1a30f0"


SRC_URI = "git://github.com/google/mediapipe.git;protocol=https;branch=master \
           file://BUILD.in \
           file://BUILD.yocto_compiler \
           file://cc_config.bzl.tpl \
           file://yocto_compiler_configure.bzl \
           file://0001-Yocto-patches.patch \
           file://0001-Fix-opencv-ffmpeg-library-paths.patch \
           file://mediapipe-config-version.cmake \
           file://mediapipe-config.cmake \
           file://mediapipe-targets-release.cmake \
           file://mediapipe-targets.cmake \
           file://0002-Build-library.patch \
           file://0008-mediapipe-cpu-target.patch \
           file://protobuf_yocto.BUILD \
           file://com_google_protobuf_use_protoc_on_path.diffforbazeltoapply \
           file://0001-instruct-bazel-to-patch-libedgetpu.patch \
           file://0001-Remove-MEDIAPIPE_OMIT_EGL_WINDOW_BIT-flag-and-autode.patch \
           file://bazel_to_cmake/mediapipe_bazel_to_cmake.py \
           file://bazel_to_cmake/pywoodfortreesgui.py \
           "

# file://0009-yocto-protobuf.patch is disabled cause it's not quite working yet for 0.8.9


inherit cmake python3native

S = "${WORKDIR}/git"

do_configure:prepend() {
    if [ ! -f ${S}/CMakeLists.txt ]
    then
        if [ -d ${S}/orig ]
        then
            cd ${S}/orig
            ${PYTHON} ${WORKDIR}/bazel_to_cmake/mediapipe_bazel_to_cmake.py mediapipe/examples/desktop/libmediapipe libmediapipe.so
            rm -rf ${S}/src
            mv out/* ${S}
            rm -rf out
        else
            cd ${S}
            ${PYTHON} ${WORKDIR}/bazel_to_cmake/mediapipe_bazel_to_cmake.py mediapipe/examples/desktop/libmediapipe libmediapipe.so
            cd ${B}
            mv ${S} ${S}.orig
            mv ${S}.orig/out ${S}
            mv ${S}.orig/oe-* ${S}
            mv ${S}.orig ${S}/orig
        fi
    fi
    # For some reason this file gets missed
    cp ${S}/orig/mediapipe/framework/port/port.h ${S}/src/mediapipe/framework/port
}



FILES:${PN} = "/opt/mediapipe/* ${bindir}/* ${libdir}/*"
INSANE_SKIP:${PN}-dev += " dev-elf "



