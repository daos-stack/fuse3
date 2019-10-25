NAME    := fuse
DEB_NAME := fuse3
SRC_EXT := gz
SOURCE   = https://github.com/libfuse/libfuse/archive/$(NAME)-$(VERSION).tar.$(SRC_EXT)
ID_LIKE := $(shell . /etc/os-release; echo $$ID_LIKE)
PATCHES := $(NAME)-install-nonroot.patch $(NAME)-linux-ioctl.patch
ifneq ($(ID_LIKE),debian)
PATCHES += $(NAME).conf
endif

include packaging/Makefile_packaging.mk