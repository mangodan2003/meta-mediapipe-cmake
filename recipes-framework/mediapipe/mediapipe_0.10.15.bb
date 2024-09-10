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
    glog \
    libeigen \
    tensorflow-lite \
    mesa \
    opencl-headers \
    mediapipe-native \
"

# NOTE: This depends on a pre-release version of tensorflow-lite (8038e44ea38bb889095afaaf6ad05e94adaed8d2) , patched as per the tflite bbappend in this repo

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

SRCREV = "e252e5667e2be398dcc4c5d49ca134248e2111c8"


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
           file://0001-add-missing-include.patch \
           "

# file://0009-yocto-protobuf.patch is disabled cause it's not quite working yet for 0.8.9


inherit cmake python3native

S = "${WORKDIR}/git"


OECMAKE_TARGET_COMPILE = "artifacts"


do_configure:prepend() {

    cd ${S}
    rm -rf src include
    ${PYTHON} ${WORKDIR}/bazel_to_cmake/mediapipe_bazel_to_cmake.py mediapipe/examples/desktop/libmediapipe mediapipe
    mv out/* ${S}
    cd ${B}

    touch ${S}/src/mediapipe/examples/desktop/libmediapipe/dummy.c
    # For some reason these files get missed
    cp ${S}/mediapipe/framework/port/port.h ${S}/src/mediapipe/framework/port
    #cp ${S}/mediapipe/util/tflite/tflite_signature_reader.h ${S}/src/mediapipe/util/tflite
    #cp ${S}/mediapipe/calculators/tensor/tflite_delegate_ptr.h ${S}/src/mediapipe/calculators/tensor
    #cp ${S}/mediapipe/calculators/tensor/inference_feedback_manager.h ${S}/src/mediapipe/calculators/tensor
    mkdir -p ${S}/src/mediapipe/framework/formats/tensor
    cp ${S}/mediapipe/framework/formats/tensor/internal.h ${S}/src/mediapipe/framework/formats/tensor
}


do_install:append() {
    # The files that mediapipe_bazel_to_cmake.py miss are also required by dependants. Manually install them..
    install ${S}/src/mediapipe/framework/port/port.h ${D}/usr/include/mediapipe/framework/port/port.h
    mv ${D}${libdir}/libmediapipe.so ${D}${libdir}/libmediapipe.so.${PV}
    ln -s libmediapipe.so.${PV} ${D}${libdir}/libmediapipe.so.0
    ln -s libmediapipe.so.0 ${D}${libdir}/libmediapipe.so
}

FILES:${PN} = "/opt/mediapipe/* ${bindir}/* ${libdir}/*"


