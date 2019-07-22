NAME    := fuse
DEB_NAME := fuse3
SRC_EXT := gz
SOURCE   = https://github.com/libfuse/libfuse/archive/$(NAME)-$(VERSION).tar.$(SRC_EXT)
ID_LIKE := $(shell . /etc/os-release; echo $$ID_LIKE)
COMMON_PATCHES := $(NAME)-install-nonroot.patch $(NAME)-linux-ioctl.patch
ifneq ($(ID_LIKE),debian)
PATCHES := $(NAME).conf $(COMMON_PATCHES)
else
PATCHES := $(COMMON_PATCHES)
endif

include Makefile_packaging.mk

