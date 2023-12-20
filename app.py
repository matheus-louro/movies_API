from flask import Flask, request, jsonify
import sqlite3

# Initialize Flask Application
app = Flask(__name__)

# Initialize cursor and connect database
def get_cursor():
    connector = sqlite3.connect("movies.db")
    connector.row_factory = sqlite3.Row
    return connector.cursor()

'''ROUTES'''

'''Get all movies'''
@app.route("/movies/")
def get_movie_byId():
    cursor = get_cursor()
    cursor.execute("SELECT * FROM movies")
    res = cursor.fetchall()
    if res:
        movies = [dict(movie) for movie in res]
        return jsonify(movies), 200
    else:
        return jsonify({'error': 'Fail to return movies'}), 500


'''
Get movies by entering the title.
example: /movies/search/title?title=The Matrix
'''
@app.route("/movies/search/title")
def get_movie_byTitle():
    try:
        title = request.args.get("title").strip()
    except AttributeError:
        return jsonify({'error': 'You must provide a title'}), 400
    
    if title:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM movies WHERE title COLLATE NOCASE = ? ORDER BY year", (title,))
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"error": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide a title'}), 400
    
'''
Get movies by year.
example: /movies/search/year?year=1999
'''
@app.route('/movies/search/year')
def get_movie_byYear():
    try:
        year = request.args.get('year').strip()
    except AttributeError:
        return jsonify({'error': 'You must provide a year'}), 400
    
    if year:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM movies WHERE year = ?", (year,))
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"error": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide a year'}), 400


'''
Get a movie by providing the director's name.
example: /movies/search/director?director=Quentin Tarantino
'''
@app.route("/movies/search/director") 
def get_movie_byDirector():
    try:
        director = request.args.get('director').strip()
    except AttributeError:
        return jsonify({'error': 'You must provide a director'}), 400
    
    if director:
        cursor = get_cursor()
        cursor.execute(
        """SELECT * FROM movies WHERE id IN (SELECT movie_id FROM directors WHERE person_id = (SELECT id FROM 
                people WHERE name COLLATE NOCASE = ? )) ORDER BY year""", (director,)
        )
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"erro": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide a director'}), 400
    

'''
Get a movie by providing the actor(s) name.
If you enter more than one actor's name, 
the API will return all the movies they acted in, not just movies where both are part of the cast
example /movies/search/actors?actors=Leonardo DiCaprio, Brad Pitt
'''
@app.route("/movies/search/actors")
def get_movie_byActors():
    try:
        actors = request.args.get('actors')
    except AttributeError:
        return jsonify({'error': 'You must provide one actor or more'}), 400

    cursor = get_cursor()
    if actors:
        if ',' in actors:
            actors = actors.split(',')
            actors_list = [actor.lstrip() for actor in actors]
            placeholders = ', '.join(['?'] * len(actors_list))
            query = f'''SELECT * FROM movies WHERE id IN (
                        SELECT movie_id FROM stars WHERE person_id IN (
                        SELECT id FROM people WHERE name COLLATE NOCASE IN ({placeholders})
                        )) ORDER BY year'''
            cursor.execute(query, tuple(actors_list))
            res = cursor.fetchall()
            if res:
                movies = [dict(movie) for movie in res]
                return jsonify(movies), 200
            else:
                
                return jsonify({"erro": "Movie(s) not found!"}), 404
            
        else:
            cursor.execute(
            '''SELECT * FROM movies WHERE id IN (SELECT movie_id FROM stars WHERE person_id = (SELECT id FROM
                people WHERE name COLLATE NOCASE = ?)) ORDER BY year''', (actors,)
            )
            res = cursor.fetchall()
            if res:
                movies = [dict(movie) for movie in res]
                return jsonify(movies), 200
            else:
                return jsonify({"erro": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide one actor or more'}), 400


'''
Get a movie by providing the cast
example: /movies/search/cast?cast=Johnny Depp, Helena Bonham Carter
'''
@app.route('/movies/search/cast')
def get_movie_byCast():
    try:
        cast = request.args.get('cast')
    except AttributeError:
        return jsonify({'error': 'You must provide the cast'}), 400
    
    if cast:
        cursor = get_cursor()
        cast = cast.split(',')
        actors = [actor.lstrip() for actor in cast]

        sub_query = '''
            SELECT movie_id
            FROM stars
            WHERE person_id IN (
                SELECT id 
                FROM people
                WHERE name COLLATE NOCASE = ?
            )
        '''
        intersect = 'INTERSECT'.join([f'{sub_query}' for _ in range(len(actors))])
        query = f'''
            SELECT * FROM movies
            WHERE id IN (
                {intersect}
            )
            ORDER BY year
        '''
        cursor.execute(query, actors)
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"erro": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide the cast'}), 400


'''
Get the cast of the movie by providing the title.
You can provide one or more actor names and the API will return the movie(s) 
which the cast includes those actors
'''
@app.route('/movies/cast')
def get_cast():
    try:
        title = request.args.get("title").strip()
    except AttributeError:
        return jsonify({'error': 'You must provide a title'}), 400
    
    if title:
        cursor = get_cursor()
        cursor.execute('''
            SELECT * FROM people
            WHERE id IN (
                SELECT person_id FROM stars
                WHERE movie_id = (
                    SELECT id FROM movies
                    WHERE title COLLATE NOCASE = ?
                )
            )
            ORDER BY name''', (title,))  
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"erro": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide a title'}), 400      

'''
Get movie statistics like rating and votes by providing the title
example: /movies/rating?title=Toy Story
'''
@app.route('/movies/rating')
def get_ratings():
    try:
        title = request.args.get("title").strip()
    except AttributeError:
        return jsonify({'error': 'You must provide a title'}), 400

    if title:
        cursor = get_cursor()
        cursor.execute('''
            SELECT * FROM ratings
            WHERE movie_id = (
                SELECT id FROM movies
                WHERE title COLLATE NOCASE = ?
            )
        ''', (title,))
        res = cursor.fetchall()
        if res:
            movies = [dict(movie) for movie in res]
            return jsonify(movies), 200
        else:
            return jsonify({"erro": "Movie(s) not found!"}), 404
    else:
        return jsonify({'error': 'You must provide a title'}), 400  
    

'''
Get the top rated movies.
you can provide a "top" parameter that will limit how many movies the API will return. 
The default value for "top" is 50
'''
@app.route('/movies/top-rated')
def get_top_rated():
    top = request.args.get('top')
    try:
        top = int(top) if top != None else 50
    except ValueError:
        return jsonify({'error': 'invalid value for top'}), 400

    cursor = get_cursor()
    cursor.execute('''
        SELECT m.*
        FROM movies m
        JOIN ratings r ON m.id = r.movie_id
        WHERE r.votes >= 1000000
        ORDER BY r.rating DESC LIMIT ?''', (top,)
    )
    
    res = cursor.fetchall()
    movies = [dict(movie) for movie in res]
    return jsonify(movies), 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
