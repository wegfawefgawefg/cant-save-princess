NAME := CantSavePrincess
SCRIPT := pyi_entry.py
PYI := pyinstaller

.PHONY: help build-linux run-linux build-macos build-windows clean distclean lint typecheck format

help:
	@echo "Make targets:"
	@echo "  build-linux   - Build onefile binary (Linux)"
	@echo "  run-linux     - Run built Linux binary"
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
		$(SCRIPT)

run-linux:
	./dist/$(NAME)

# macOS build (must run on macOS)
build-macos:
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--onefile --windowed \
		--add-data "sounds:sounds" \
		$(SCRIPT)

# Windows build (must run on Windows; note semicolon in --add-data)
build-windows:
	@echo "Run this target on Windows (PyInstaller doesn't cross-compile)."
	uv run $(PYI) \
		--clean --noconfirm \
		--name $(NAME) \
		--onefile --windowed \
		--add-data "sounds;sounds" \
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
