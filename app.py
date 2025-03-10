from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)




########################################################################################################################
##  Functions:                                                                                                           ##
########################################################################################################################




# This function will get a list of all games so that it can be displayed on the main landing page:
def get_all_games():
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT game_id, game_name, description FROM games")
    games = cursor.fetchall()
    conn.close()
    return games

# This function will get a specific games details:
def get_game_details(game_id):
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, description FROM games WHERE game_id = ?", (game_id,))
    game = cursor.fetchone()
    conn.close()
    return game

# This function will get a games leaderboard details:
def get_leaderboard_data(game_name):
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT game_id FROM games WHERE game_name = ?", (game_name,))

    # Fetch the result
    result = cursor.fetchone()

    # Check if a result was found
    if result:
        game_id = result[0]
    else:
        game_id = None

    cursor.execute("""
    SELECT rank, player_name, score FROM leaderboard
    WHERE game_id = ?
    ORDER BY rank ASC
    """, (game_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def test_get_leaderboard_data(game_id):
    # Connect to the SQLite database (using an in-memory database for testing)
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create the games and leaderboard tables
    cursor.execute('''
    CREATE TABLE games (
        game_id INTEGER PRIMARY KEY,
        game_name TEXT,
        description TEXT
    )''')

    cursor.execute('''
    CREATE TABLE leaderboard (
        leaderboard_id INTEGER PRIMARY KEY,
        game_id INTEGER,
        player_name TEXT,
        score INTEGER,
        rank INTEGER,
        FOREIGN KEY (game_id) REFERENCES games(game_id)
    )''')

    # Insert example data
    cursor.execute("INSERT INTO games (game_name, description) VALUES ('Game A', 'A fun game')")
    cursor.execute("INSERT INTO leaderboard (game_id, player_name, score, rank) VALUES (1, 'Player1', 100, 1)")
    cursor.execute("INSERT INTO leaderboard (game_id, player_name, score, rank) VALUES (1, 'Player2', 90, 2)")
    cursor.execute("INSERT INTO leaderboard (game_id, player_name, score, rank) VALUES (1, 'Player3', 80, 3)")

    # Fetch the leaderboard data ordered by rank
    cursor.execute('''
    SELECT rank, player_name, score FROM leaderboard
    WHERE game_id = ?
    ORDER BY rank ASC
    ''', (game_id,))

    leaderboard_data = cursor.fetchall()

    conn.close()

    return leaderboard_data

# Add user score to the leaderboard:
def add_leaderboard_entry(game_name, player_name, score, rank):
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leaderboard (game_id, player_name, score, rank)
        VALUES ((SELECT game_id FROM games WHERE game_name = ?), ?, ?, ?);
    ''', (game_name, player_name, score, rank))
    conn.commit()
    conn.close()

# This function will add a new game to the database:
def add_game_to_db(game_name, description):
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO games (game_name, description) VALUES (?, ?)", (game_name, description))
    conn.commit()
    conn.close()

# This function will remove a game from the database:
def delete_game_from_db(game_id):
    conn = sqlite3.connect('MSD-P01-LeaderBoard.sqlite')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
    conn.commit()
    conn.close()




########################################################################################################################
##  Routes:                                                                                                           ##
########################################################################################################################




# Main landing page route with GET and POST to allow for adding games to the database:
@app.route('/', methods=['GET', 'POST'])
def home():
    # Display all games
    games = get_all_games()  # Fetch all games from the database
    return render_template('index.html', games=games)


# Leaderboard for an individual game:
@app.route('/leaderboard/<game_name>', methods=['GET', 'POST'])
def leaderboard(game_name):
    if request.method == 'POST':
        # If the form is submitted, insert the new leaderboard entry
        player_name = request.form['player_name']
        score = request.form['score']
        rank = request.form['rank']
        add_leaderboard_entry(game_name, player_name, score, rank)
        return redirect(url_for('leaderboard', game_name=game_name))

    # GET request: display the leaderboard for the specific game
    leaderboard_data = get_leaderboard_data(game_name)
    return render_template('leaderboard.html', game_name=game_name, leaderboard=leaderboard_data)

# Route to a games details page:
@app.route('/game/<int:game_id>')
def game_details(game_id):
    game = get_game_details(game_id)
    if game:
        return render_template('game_details.html', game=game)
    else:
        return "Game not found", 404

# Add the game to the database:
@app.route('/add_game', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        # Get form data for the new game
        game_name = request.form['game_name']
        description = request.form['description']

        # Insert new game into the database
        add_game_to_db(game_name, description)

        # Redirect to the homepage to show the updated list of games
        return redirect(url_for('home'))

# Delete the game listed in the database:
@app.route('/delete_game/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    delete_game_from_db(game_id)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
