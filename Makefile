NAME := CantSavePrincess
SCRIPT := pyi_entry.py
PYI := pyinstaller

.PHONY: help build-linux build-linux-dir run-linux build-macos build-windows clean distclean lint typecheck format

help:
	@echo "Make targets:"
	@echo "  build-linux       - Build onefile binary (Linux)"
	@echo "  build-linux-dir   - Build onedir app (Linux; easier to debug)"
	@echo "  run-linux         - Run built Linux binary (onefile or onedir)"
	@echo "  build-macos   - Build onefile app (macOS)"
	@echo "  build-windows - Build onefile exe (Windows; run on Windows)"
	@echo "  clean         - Remove build artifacts"
	@echo "  distclean     - Clean and remove PyInstaller spec"
	@echo "  lint          - Run Ruff lint checks"
	@echo "  format        - Run Ruff formatter"
	@echo "  typecheck     - Run mypy (and pyright if available)"

# Linux build (also fine on macOS syntax-wise)
build-linux:
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--onefile --noconsole \
		--add-data "sounds:sounds" \
		--add-data "sprites:sprites" \
		$(SCRIPT)

# Linux build (onedir; easier to inspect assets and files)
build-linux-dir:
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--noconsole \
		--add-data "sounds:sounds" \
		--add-data "sprites:sprites" \
		$(SCRIPT)

run-linux:
	@if [ -x ./dist/$(NAME) ]; then \
		echo "Running onefile: dist/$(NAME)"; \
		./dist/$(NAME); \
	elif [ -x ./dist/$(NAME)/$(NAME) ]; then \
		echo "Running onedir: dist/$(NAME)/$(NAME)"; \
		./dist/$(NAME)/$(NAME); \
	else \
		echo "No Linux build found. Run 'make build-linux' or 'make build-linux-dir' first."; \
		exit 1; \
	fi

# macOS build (must run on macOS)
build-macos:
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--onefile --windowed \
		--add-data "sounds:sounds" \
		--add-data "sprites:sprites" \
		$(SCRIPT)

# Windows build (must run on Windows; note semicolon in --add-data)
build-windows:
	@echo "Run this target on Windows (PyInstaller doesn't cross-compile)."
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--onefile --windowed \
		--add-data "sounds;sounds" \
		--add-data "sprites;sprites" \
		$(SCRIPT)

clean:
	rm -rf build dist

distclean: clean
	rm -f *.spec

lint:
	uv run ruff check .

format:
	uv run ruff format src

typecheck:
	uv run mypy . || true
	# Run pyright if installed (will not fail CI if missing)
	pyright || true
