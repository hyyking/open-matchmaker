run:
	@python -m bot

render:
	pandoc --mathjax project/README.md -o project.pdf

tree:
	@tree --dirsfirst -I "__pycache__"
