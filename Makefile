STOW_DIR := stow
TARGET   := $(HOME)
PACKAGES := $(notdir $(wildcard $(STOW_DIR)/*))

STOW := $(shell command -v stow 2>/dev/null)

ifeq ($(STOW),)
$(error "stow not found. Install GNU Stow first.")
endif

.PHONY: install uninstall restow adopt list

install:
	stow -d $(STOW_DIR) -t $(TARGET) $(PACKAGES)

uninstall:
	stow -d $(STOW_DIR) -t $(TARGET) -D $(PACKAGES)

restow:
	stow -d $(STOW_DIR) -t $(TARGET) -R $(PACKAGES)

adopt:
	stow -d $(STOW_DIR) -t $(TARGET) --adopt $(PACKAGES)

list:
	@printf "%s\n" $(PACKAGES)
