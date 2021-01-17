# Baby'Haxball MatchMaker

![Affiche](static/affiche.png)

## Usage

Beware that the system is made to be used with an even number of teams

1. Generate database (see database script)
2. Add teams (see database script)
3. Add players (see database script)
4. Check with `./insert.py summary`
5. Generate pairs with `./matchmaking.py {turn}`
6. Generate the played round and insert results (see mock data script)
7. Check data with `./insert.py matches`

## System

> [french article](PROJECT.md)

The system is based around an elo model with a seasonal parameter. Model constants
are found in the `matchmaking.py` file.

Summary:

```
ELO:
  BASE_ELO = 1000
  K = 16
  PPM = 7    // points per match

SEASONAL:
  PERIOD = 3 // every 3 period the seasonal parameter is on
  DUTY_CYCLE = 0.2 // length of the activity (corresponds to one period)
```

The seasonal parameter's purpose is to reduce the distance between higher and lower
ranked teams. And thus add distance to teams with similar ranks. This adds a bit of
variance between matches and allows lower teams to upset and gain more elo.


