NAME := CantSavePrincess
SCRIPT := pyi_entry.py
PYI := pyinstaller

.PHONY: help build-linux run-linux build-macos build-windows clean distclean

help:
	@echo "Make targets:"
	@echo "  build-linux   - Build onefile binary (Linux)"
	@echo "  run-linux     - Run built Linux binary"
	@echo "  build-macos   - Build onefile app (macOS)"
	@echo "  build-windows - Build onefile exe (Windows; run on Windows)"
	@echo "  clean         - Remove build artifacts"
	@echo "  distclean     - Clean and remove PyInstaller spec"

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
