WIN_DELTA = 25
LOSS_DELTA = -20
DRAW_DELTA = 5
UPSET_BONUS = 10


def calculate_elo_change(winner_rating, loser_rating, is_draw=False, winner_is_first=True):
    if is_draw:
        return DRAW_DELTA, DRAW_DELTA

    winner_delta = WIN_DELTA
    loser_delta = LOSS_DELTA

    if winner_rating < loser_rating:
        winner_delta += UPSET_BONUS

    if winner_is_first:
        return winner_delta, loser_delta
    return loser_delta, winner_delta
