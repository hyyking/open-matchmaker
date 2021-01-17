#! /bin/sh

rm db.sqlite3
sqlite3 db.sqlite3 < tables.sql

./insert.py team "Koba la Defaite"
./insert.py team "LES RESERVISTES"
./insert.py team "Les snipers"
./insert.py team "95 GANG"
./insert.py team "FC Zizou"
./insert.py team "Les micros d'argent"
./insert.py team "Les gagnants"
./insert.py team "Les devin-si"

./insert.py player "Koba la Defaite" "Leo"
./insert.py player "Koba la Defaite" "Victoire"
./insert.py player "LES RESERVISTES" "Lou"
./insert.py player "LES RESERVISTES" "Pauline"
./insert.py player "Les snipers" "Daniel"
./insert.py player "Les snipers" "Manon"
./insert.py player "95 GANG" "Gregoire"
./insert.py player "95 GANG" "Lise"
./insert.py player "FC Zizou" "Carl"
./insert.py player "FC Zizou" "Matthieu"
./insert.py player "Les micros d'argent" "Simon"
./insert.py player "Les micros d'argent" "Paul"
./insert.py player "Les gagnants" "Arnaud"
./insert.py player "Les gagnants" "Margaux"
./insert.py player "Les devin-si" "Leonard"
./insert.py player "Les devin-si" "Kristina"
