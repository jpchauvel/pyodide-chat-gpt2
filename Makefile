.PHONY: build serve clean

build: build/app.tar.gz

build/app.tar.gz: main.py
	mkdir -p build
	tar -czf build/app.tar.gz main.py

serve: build
	python3 -m http.server 8080

clean:
	rm -rf build
