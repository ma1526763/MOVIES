from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
import os
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired

MOVIE_API_KEY = os.environ['MOVIE_KEY']
MOVIE_SEARCH_ENDPOINT = 'https://api.themoviedb.org/3/search/movie'

app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.String(100), nullable=True)
    review = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)


db.create_all()


class editForm(FlaskForm):
    rating = FloatField("Your rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your review", validators=[DataRequired()])
    done = SubmitField("Done")


class addMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    add = SubmitField('ADD MOVIE')


@app.route("/")
def home():
    movie_data = Movies.query.order_by(Movies.rating).all()[::-1]
    for i, movie in enumerate(movie_data):
        movie.ranking = str(i + 1)
        db.session.commit()
    return render_template("index.html", movies=movie_data)


@app.route("/edit?id=<int:movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    print("EDIT", movie_id)
    movie_data = Movies.query.get(movie_id)
    form = editForm()
    if form.validate_on_submit():
        rating = request.values['rating']
        movie_data.rating = rating
        movie_data.review = request.values['review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_data, form=form)


@app.route("/delete?id=<int:movie_id>")
def delete(movie_id):
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = addMovie()
    next_movie_id = len(Movies.query.all()) + 1
    if form.validate_on_submit():
        params = {
            'api_key': MOVIE_API_KEY,
            'query': request.values['title'],
            'language': 'en-US',
            'page': 1,
        }
        movie_page_data = requests.get(MOVIE_SEARCH_ENDPOINT, params=params).json()['results']
        return render_template('select.html', movies_data=movie_page_data, next_movie_id=next_movie_id)
    return render_template("add.html", form=form)


@app.route('/add<int:movie_id>')
def add_movie_to_db(movie_id):

    params = {
        'api_key': MOVIE_API_KEY,
    }
    movie_data = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}', params=params).json()
    new_movie = Movies(
        title=movie_data['title'],
        year=int(movie_data["release_date"].split("-")[0]),
        description=movie_data['overview'],
        rating=0,
        ranking='',
        review="",
        img_url=f"https://image.tmdb.org/t/p/w500/{movie_data['poster_path']}")
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', movie_id=len(Movies.query.all())))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
