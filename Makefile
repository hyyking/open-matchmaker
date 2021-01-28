DATABASE = matchmaker.sqlite3
SQL = matchmaker_db.sql

run:
	@python -m bot
db:
	@sqlite3 $(DATABASE) < $(SQL)
tree:
	@tree --dirsfirst -I "__pycache__"
