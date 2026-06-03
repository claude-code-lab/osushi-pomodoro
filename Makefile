.PHONY: install uninstall

SCRIPT_DIR := $(shell pwd)
OSUSHI_PY  := $(SCRIPT_DIR)/osushi.py

RC_FILE := $(shell \
	if [ "$$(basename "$$SHELL")" = "zsh" ]; then \
		if [ -n "$$ZDOTDIR" ]; then echo "$$ZDOTDIR/.zshrc"; \
		else echo "$$HOME/.zshrc"; fi; \
	elif [ "$$(basename "$$SHELL")" = "bash" ]; then echo "$$HOME/.bashrc"; \
	else echo "$$HOME/.profile"; fi)

install:
	@chmod +x "$(OSUSHI_PY)"
	@echo "🍣 時すでにおすし インストーラー"
	@MARKER='# 時すでにおすし'; \
	ALIAS="alias osushi='python3 $(OSUSHI_PY)'"; \
	if grep -qF "$$MARKER" "$(RC_FILE)" 2>/dev/null; then \
		echo "✅ すでにインストール済みです: $(RC_FILE)"; \
	else \
		printf '\n%s\n%s\n' "$$MARKER" "$$ALIAS" >> "$(RC_FILE)"; \
		echo "✅ エイリアスを追加しました: $(RC_FILE)"; \
	fi
	@echo ""
	@echo "設定を反映するには: source $(RC_FILE)"

uninstall:
	@echo "🗑️  時すでにおすし アンインストーラー"
	@MARKER='# 時すでにおすし'; \
	if grep -qF "$$MARKER" "$(RC_FILE)" 2>/dev/null; then \
		grep -vF "$$MARKER" "$(RC_FILE)" | grep -v 'alias osushi=' > "$(RC_FILE).tmp" && mv "$(RC_FILE).tmp" "$(RC_FILE)"; \
		echo "✅ エイリアスを削除しました: $(RC_FILE)"; \
	else \
		echo "ℹ️  インストールされていません: $(RC_FILE)"; \
	fi
	@echo ""
	@echo "設定を反映するには: source $(RC_FILE)"
