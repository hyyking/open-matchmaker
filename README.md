# Baby'Haxball MatchMaker

![Affiche](project/static/affiche.png)

## Usage

1. Create a discord bot
2. Set token environment variable (`export DISCORD_TOKEN = ?`)
3. Run with `make run`

## System

> [french article](project/PROJECT.md)

The system is based around an elo model with a seasonal parameter. Model constants
are found in the `matchmaking/matchmaking.py` file.

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
