NAME    := fuse
DEB_NAME := fuse3
SRC_EXT := gz
ID_LIKE := $(shell . /etc/os-release; echo $$ID_LIKE)

include packaging/Makefile_packaging.mk