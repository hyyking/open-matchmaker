# Baby'Haxball Matchmaker

## Introduction

Ce projet a été écrit dans le cadre du cours de python M1 ISF et du tournoi
[haxball](https://www.haxball.com/) (jeu de foot en ligne) organisé avec l'association Baby'Assas du 20
novembre 2020.

Le but était d'organiser une suite de matchs et determiner la meilleure équipe. Afin de jouer le
maximum de matchs possibles, j'ai décidé de ne pas utiliser un format de tournoi classique qui limitent
les rencontres entre les équipes. En effet sur un format classique les gagnants jouent les gagnants,
une option aurai été d'utiliser un tournoi à 2-3 éliminations mais les novices sont tout de même rapidement
éliminés.

Une manière de regler ce problème est d'éstimer le niveau des équipes et de faire des matchs équilibrés.
De cette manière les matchs sont équilibrés, permettent de comparer les niveaux et font jouer toutes les
équipes constament.

\pagebreak
## Le modèle
Afin d'éstimer le niveau des équipes j'ai mis en place un système d'[élo](https://en.wikipedia.org/wiki/Elo_rating_system),
système initialement utilisé par les joueurs d'échecs puis étendu plus largement aux jeux en ligne.
L'avantage de ce système est que l'élo est propre à chaque équipe, il represente le niveaux théorique de
l'équipe en la plaçant sur un quantile de distribution.  Par la loi centrale limite les équipes
convergent vers leur élo réel et la distribution des équipes est gaussienne. Ainsi l'ajout et le retrait
d'une équipe n'affecte pas les scores ni le format du tournoi.

Pour initiliser une équipe on lui affecte l'élo moyen, il s'agit du premier paramètre du modèle,
`BASE_ELO = 1000` dans notre cas. Ensuite l'estimation du vainqueur se fait en comparant les élos.
Le calcul des probabilités est donné par la formule de la courbe logistique, $R_i$ étant l'élo de
l'équipe $i$:

$$ E_a =  \frac{1}{1 + 10^{(R_b - R_a)/400}} $$
$$ E_b =  \frac{1}{1 + 10^{(R_a - R_b)/400}} $$

Dans le code python:

```python
@dataclass
class Team:
    """ abstraction of the `team` table """
    code: int
    name: str
    elo: float

    def expected_score(self, other: Team) -> float:
        """ compute expected score according to the elo formula """
        return round((1 / ( 1 + 10**((other.elo - self.elo)/400))) * PPM, 2)
```

Aux échecs on marque les victoires par `1`, les échecs par `0` et les égalités par `0.5`, donnant ansi
une estimation de la probabilité de victoire. Dans notre cas les matchs étaient joués en `7` points, on multiplie l'estimation par le nombre de points par matchs (le deuxième paramètre `PPM = 7`) ce qui donne le
nombre de points éstimés pour l'équipe $i$. La mise à jour de l'élo est faite par la formule:

$$ \tilde{R}_i = R_i + K * (S_i - E_i) $$

Où facteur `K` (dans le modèle `K = 16`) est le facteur d'ajustement de l'élo et $S_a$ est le score obtenu.
Ainsi une défaite avec un score supérieur au score attendu fait augmenter l'élo de l'équipe.

\pagebreak
## La base de donnée

Les données sont stockés dans une base de donnée `sqlite3`, l'avantage est le stockage sur un fichier et
la présence de l'interface dans la librairie standart de python. La base de donnée est composé de 4 tableaux.
Le tableau de résultat stocke l'élo avant le match, permettant de charger l'état du monde en récupérant
seulement les résultats du round précédent. Une option aurait été de stocker
$$\Delta R_i = \tilde{R}_i - R_i = K * (S_i - E_i) $$ pour chaque match, solution plus efficace pour un
faible nombre de matchs.

Les tableaux sont présentés ci-dessous:

```sql
CREATE TABLE IF NOT EXISTS player (
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    team INT NOT NULL,
    name VARCHAR(16) NOT NULL,

    FOREIGN KEY (team) REFERENCES team(code)
);

CREATE TABLE IF NOT EXISTS team (
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(16) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS result (
    turn INT NOT NULL,
    team1 INT NOT NULL,
    team2 INT NOT NULL,
    elo1 FLOAT NOT NULL,
    elo2 FLOAT NOT NULL,
    points1 INT,
    points2 INT,

    PRIMARY KEY(turn, team1, team2),
    FOREIGN KEY (turn) REFERENCES turn(code),
    FOREIGN KEY (team1) REFERENCES team(code),
    FOREIGN KEY (team2) REFERENCES team(code)
);

```
```sql
CREATE TABLE IF NOT EXISTS turn (
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL
);
```
\pagebreak

## L'appariement

Le modèle d'appariement est plutôt simple, il s'agit d'une maximisation de l'utilité d'un agent principal.
Ici le principal est le programme et la fonction d'utilité est la somme des utilités marginales des matchs.

L'utilité est également dépendente d'un paramètre saisonier. En effet avec un système d'élo les équipes
avec un élo proche jouent les unes contres le autres, or dans le cas d'un tournoi amicale il est préférable
que toutes les équipes se rencontrent. Ainsi j'ai mis en place ce paramètre qui augmente périodiquement l'utilité des matchs déséquilibré.

La fonction d'utilité d'un match est donnée par:

$$ U(E_a, E_b, i) = \exp\{-|E_a - E_b|\} + \frac{p(i)}{\exp\{-|E_a - E_b|\}} $$

Avec p(i) une fonction sinusoïdale carré active (1) en T pendant D et 0 sinon. T représente la période de la fonction et D le temps d'activation. Dans le modèle `T = 3` et `D = 0.2`, soit toutes les 3 périodes
pendant 1 période. La fonction est représentée ci-dessous en temps discret:

![p(i)](./static/sin.png)

Le choix d'une fonction exponentielle négative composée avec la valeur absolue permet de garantir que l'écart
est pris en valeur absolue (positif) et donc que l'utilité est décroissante avec la distance. Le paramètre
saisonier inverse cette relation lorsque `p(i) = 1`, en effet l'exponentielle négative donne une valeur
comprise en 0 et 1 donc diviser permet d'augment l'effet du paramètre lorsque la distance est grande.

L'équivalent dans le code python:

```python
@dataclass
class Match:
    """ A match is a pair of teams at a fixed turn """
    turn: int
    team1: Team
    team2: Team

    def utility(self) -> float:
        """ compute principal's utility of the match """
        escore1 = self.team1.expected_score(self.team2)
        escore2 = self.team2.expected_score(self.team1)
        distance = math.exp(-abs(escore1 - escore2)) # ]0; 1[
        return distance + (self.period() / distance) # ]0; +inf[

    def period(self) -> float:
        """ compute periodic factor for the turn: {0, 1} """
        turn = self.turn * 100
        return max((-1) ** int((turn % T)/T >= D), 0)

@dataclass(repr=False)
class Set:
    """ A set represents all matches played in a turn """
    matches: List[Match]

    def utility(self) -> float:
        """ compute principal's utility of the set """
        return sum(map(lambda x: x.utility(), self.matches))
```

\pagebreak

L'algorithme d'appariement est alors le suivant:

* Si le tour est 0: Créer un set aléatoirement 
* Si le tour est != 0:
  1. Generer tous les matchs possibles
  2. Soustraire les matchs joués les n derniers rounds (pour eviter les sets équivalents n=T+1)
  3. Generer tous les sets possibles (combinaisons d'ordre $n % 2 == 0$)
  4. Filtrer les sets impossibles (une équipe joue plus d'une fois)
  5. Choisir le set apportant le plus d'utilité 

En python:

```python
def appear_once(matches) -> bool:
    teams = set()
    for match in matches:
	team1 = match.team1
	team2 = match.team2
	if team1 in teams or team2 in teams:
	    return False
	teams.add(team1)
	teams.add(team2)
    return True

def match(conn, turn):
    if turn == 1:
	# Le premier round est aléatoire
	import random # pylint: disable=C0415
	rteams =  [
	    Team(*x, elo=BASE_ELO)
	    for x in conn.execute("SELECT * FROM team").fetchall()
	]
	random.shuffle(rteams)
	set = Set((Match(turn, *rteams[i:i+2]) for i in range(0, len(rteams), 2))

    else:
	p_matches = { Match(turn, *teams) for teams in it.combinations(teams, 2) } # 1.
	p_matches.difference_update(PREV_MATCHES) # 2.
	p_sets = [ # 3.
	    Set(matches)
	    for matches in it.combinations(p_matches, int(len(teams)/2))
	    if appear_once(matches) # 4.
	] 
	set = max(p_sets).matches # 5.
    return set
```

\pagebreak
## Le programme

Le programme est décomposé en deux scripts, le premier avec les opérations sur la base de donnée et le
deuxième pour générer les matchs. Avec le module `argparse` on récupere les information via le terminal.

Commandes d'insertion:
```shell
>>> python insert.py --help
usage: insert.py [-h]
                 {team,player,result,turn,summary,matches} ...

Add values to the database

positional arguments:
  {team,player,result,turn,summary,matches}
    team                add a team to the database
    player              add a player to the database
    result              add a result to the database
    turn                add a turn to the data database
    summary             display players and teams
    matches             display turns and results

optional arguments:
  -h, --help            show this help message and exit```
```

Commandes d'appariement:
```shell
>>> python matchmaker.py --help
usage: matchmaker.py [-h] turn

Generate match pairs for next turn

positional arguments:
  turn

optional arguments:
  -h, --help  show this help message and exit
```

\pagebreak
### Exemple:
_Insertion_:
```
./insert.py team "Koba la Défaite"
...
./insert.py team "Les devin-si"

./insert.py player "Koba la Défaite" "Léo"
./insert.py player "Koba la Défaite" "Victoire"
...
./insert.py player "Les devin-si" "Leonard"
./insert.py player "Les devin-si" "Kristina"
```

_Déroulement_:
```
./insert.py turn # turn 1
./insert.py result 1 "Koba la Défaite" "LES RESERVISTES" "7-4" 
./insert.py result 1 "Les snipers" "Les devins-si" "5-7" 
./insert.py result 1 "95 GANG" "FC Zizou" "7-2" 
./insert.py result 1 "Les micros d'argent" "Les gagnants" "0-7" 
./matchmaker.py 2

Lecture: A(R_a) VS B(R_b) ~ E_a-E_b
>>> Koba la Défaite(1056.0) VS LES RESERVISTES(1056.0) ~ 3.5-3.5
>>> Les micros d'argent(1008.0) VS Les devin-si(960.0) ~ 3.98-3.02
>>> Les snipers(1056.0) VS Les gagnants(1056.0) ~ 3.5-3.5
>>> FC Zizou(1040.0) VS 95 GANG(1024.0) ~ 3.66-3.34

./insert.py turn # turn 2
./insert.py result 2 "Les devins-si" "LES RESERVISTES" "7-3" 
./insert.py result 2 "Les snipers" "Koba la Défaite" "7-2" 
./insert.py result 2 "Les micros d'argent" "FC Zizou" "6-7" 
./insert.py result 2 "95 GANG" "Les gagnants" "4-7" 
./matchmaker.py 3 ...
```

## Conclusion
Le programme a été utilisé avec succès lors de l'evènement. En tant que joueurs j'ai vu la qualité des
matchs s'améliorer passé les 3 premiers match. L'impact du paramètre saisonnier était largement visible dans
les resultats des matchs multiples de 3. Le paramètre d'ajustement (`K`) était assez faible pour maintenir
des élos proches et créer de la competition.
Cependant le programme a tout de même des problèmes: il faut un nombre pair d'équipes, il faut également 
ajouter des rounds à la main. Enfin si le paramètre d'historique est mal paramétré on peut se retrouver
avec un graphe disjoint d'ordre impair implicant qu'il est impossible de former un nombre pair de matchs.
